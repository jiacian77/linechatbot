"""LINE Messaging API webhook with Gemini text and image replies."""

import io
import logging
import os
from collections import defaultdict

import requests
from dotenv import load_dotenv
from flask import Flask, abort, request
from google import genai
from google.genai import types
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import ImageMessageContent, MessageEvent, TextMessageContent
from PIL import Image

load_dotenv()

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN", "")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
PORT = int(os.getenv("PORT", "8080"))

missing = [
    name
    for name, value in (
        ("CHANNEL_ACCESS_TOKEN", CHANNEL_ACCESS_TOKEN),
        ("CHANNEL_SECRET", CHANNEL_SECRET),
        ("GEMINI_API_KEY", GEMINI_API_KEY),
    )
    if not value
]
if missing:
    raise RuntimeError("請先在 .env 設定：" + ", ".join(missing))

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

line_config = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
gemini = genai.Client(api_key=GEMINI_API_KEY)
sessions = defaultdict(list)
system_instruction = (
    "你是一個友善的 LINE 聊天機器人，請使用繁體中文回答。"
    "回答清楚、精簡；LINE 不支援 Markdown 時，請用 emoji 和純文字排版。"
)


def reply_text(reply_token: str, text: str) -> None:
    # LINE reply messages have a 5000-character limit.
    text = (text or "目前無法產生回覆，請稍後再試。")[:4900]
    with ApiClient(line_config) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=text)],
            )
        )


def ask_gemini(user_id: str, prompt: str, image: Image.Image | None = None) -> str:
    history = sessions[user_id]
    contents = []
    for old_prompt, old_answer in history[-8:]:
        contents.extend(
            [
                types.Content(role="user", parts=[types.Part(text=old_prompt)]),
                types.Content(role="model", parts=[types.Part(text=old_answer)]),
            ]
        )
    parts = [types.Part(text=prompt)]
    if image is not None:
        parts.insert(0, types.Part(inline_data=types.Blob(mime_type="image/jpeg", data=_jpeg_bytes(image))))
    contents.append(types.Content(role="user", parts=parts))
    response = gemini.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            max_output_tokens=1200,
        ),
    )
    answer = (response.text or "我暫時沒有產生文字回覆，請換個方式問我。").strip()
    history.append((prompt, answer))
    del history[:-8]
    return answer


def _jpeg_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/callback")
def callback():
    signature = request.headers.get("X-Line-Signature")
    if not signature:
        abort(400, "Missing LINE signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.warning("LINE webhook signature validation failed")
        abort(400)
    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    user_id = getattr(event.source, "user_id", None) or "anonymous"
    try:
        answer = ask_gemini(user_id, event.message.text)
    except Exception:
        app.logger.exception("Gemini text request failed")
        answer = "抱歉，我現在連不上 AI 服務，請稍後再試。"
    reply_text(event.reply_token, answer)


@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event):
    user_id = getattr(event.source, "user_id", None) or "anonymous"
    url = f"https://api-data.line.me/v2/bot/message/{event.message.id}/content"
    try:
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"},
            timeout=(5, 30),
        )
        response.raise_for_status()
        image = Image.open(io.BytesIO(response.content))
        answer = ask_gemini(user_id, "請描述這張圖片，並用繁體中文回答。", image)
    except Exception:
        app.logger.exception("LINE image handling failed")
        answer = "抱歉，我目前無法分析這張圖片，請稍後再試。"
    reply_text(event.reply_token, answer)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)

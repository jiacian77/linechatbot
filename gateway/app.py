"""LINE webhook gateway: validate signatures and forward events to n8n."""

import base64
import hashlib
import hmac
import logging
import os

import requests
from flask import Flask, abort, request

CHANNEL_SECRET = os.environ.get("CHANNEL_SECRET", "")
N8N_WEBHOOK_URL = os.environ.get(
    "N8N_WEBHOOK_URL", "http://n8n:5678/webhook/linebot-inbound"
)
PORT = int(os.environ.get("PORT", "8080"))

if not CHANNEL_SECRET:
    raise RuntimeError("CHANNEL_SECRET must be set")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.post("/line/webhook")
def line_webhook():
    # Keep the raw body cached so get_json() can parse the same bytes after
    # signature validation.
    body = request.get_data(cache=True)
    signature = request.headers.get("X-Line-Signature", "")
    expected = base64.b64encode(
        hmac.new(CHANNEL_SECRET.encode(), body, hashlib.sha256).digest()
    ).decode()
    if not signature or not hmac.compare_digest(expected, signature):
        app.logger.warning("Rejected LINE webhook with invalid signature")
        abort(400)

    # LINE may send an empty event list during the Console Verify check.
    try:
        payload = request.get_json(force=False, silent=False)
    except Exception:
        abort(400)
    if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
        abort(400)
    if not payload["events"]:
        return "OK", 200

    try:
        forwarded = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=(3, 10),
        )
        forwarded.raise_for_status()
    except requests.RequestException:
        app.logger.exception("Could not forward a LINE event to n8n")
        abort(502)
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)

# LINE Gemini Bot

依照 [HackMD 教學](https://hackmd.io/@chenmoucheng/linebot-by-codex#/1) 的流程建立：LINE Messaging API webhook、Gemini 繁體中文對話、圖片理解。使用環境變數保存憑證。

## Windows 本機啟動

1. 安裝 Python 3.10+ 和 Node.js。
2. 在 PowerShell 開啟本資料夾，執行：

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   Copy-Item .env.example .env
   notepad .env
   ```

3. 在 `.env` 填入 LINE Developers 的 Channel access token、Channel secret，以及 Google AI Studio 的 API key。
4. 啟動程式：

   ```powershell
   python bot.py
   ```

5. 開另一個 PowerShell 視窗，執行 `npx localtunnel --port 8080`。若要固定子網域，可使用 `npx localtunnel --port 8080 --subdomain 你選的名稱`。
6. 將隧道網址加上 `/callback`，填入 LINE Developers 的 Webhook URL，啟用 Use webhook，並使用 Verify 確認。
7. 到 LINE Official Account Manager 關閉不需要的自動回應／Greeting message，以免與程式回覆重複。

健康檢查網址為 `http://localhost:8080/health`。Webhook 為 `/callback`。程式支援文字和圖片訊息，對話脈絡保留在記憶體中，程式重啟後會清除。

## LINE 憑證取得

- 在 LINE Developers Console 的 Messaging API channel 查看 Channel secret，並簽發 Channel access token。
- 在 Google AI Studio 建立 Gemini API key。
- 請勿將 `.env` 或任何金鑰加入 Git，也不要把金鑰貼到公開聊天室。

# LINE Gemini Bot（Docker Compose + n8n）

本專案依照[老師的 HackMD 投影片](https://hackmd.io/@chenmoucheng/linebot-by-codex#/1)，在 Windows PC 以 Docker Compose 執行 n8n、LINE webhook gateway 與 Tailscale Funnel，再由 Gemini 提供雲端模型回覆。架構細節與驗收步驟請看 [plan.md](plan.md)。

## Windows 啟動

1. 開啟 Docker Desktop，等待 Linux engine 啟動。
2. 在 PowerShell 執行一次：

   ```powershell
   .\scripts\configure.ps1
   ```

   這會在本機 `.env` 產生 n8n 的加密金鑰，不會輸出金鑰值。
3. 確認 `.env` 已有 LINE `CHANNEL_ACCESS_TOKEN`、`CHANNEL_SECRET`、Google `GEMINI_API_KEY`。Tailscale 會用互動式登入加入，不需要 auth key。切勿分享 `.env`。
4. 啟動容器：

   ```powershell
   docker compose up -d --build
   docker compose ps -a
   ```

5. 開啟 `http://localhost:5678`，建立本機 n8n 管理帳號，找到並發布 `LINE stateless text chatbot`。
6. 執行 `.\scripts\connect-tailscale.ps1` 開啟互動式登入視窗，在已登入的 Tailscale 瀏覽器開啟該視窗顯示的連結並確認加入 `linebot` 裝置。授權完成後，啟用 Funnel 並取得公開 HTTPS 網址：

   ```powershell
   docker compose exec tailscale tailscale funnel --bg http://127.0.0.1:8080
   docker compose exec tailscale tailscale funnel status
   ```

7. 在 LINE Developers 設定 Webhook URL 為 `https://你的 Funnel 網址/line/webhook`，Verify 成功後開啟 Use webhook。測試前確認官方帳號自動回應與歡迎訊息關閉。

## 架構與限制

- Gateway 驗證 LINE 簽章後轉交 n8n；workflow 篩選文字、去重、呼叫 Gemini 並透過 LINE Reply API 回覆。
- 依老師投影片採 stateless 設計，只處理當次文字；貼圖、圖片、影片、語音不回覆，也不保留短期記憶。
- n8n UI 僅綁定本機 `127.0.0.1:5678`；公開 Funnel 只連到 gateway。
- 成功與失敗執行內容不保存。`.env`、LINE/Gemini 憑證不得加入 Git 或貼到公開聊天室。
- `docker compose down` 保留資料；`docker compose down -v` 會刪除 n8n 與 Tailscale volume。

詳細步驟、組態與驗收清單見 [plan.md](plan.md)。

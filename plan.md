---
title: LINE Bot：Docker Compose、n8n 與 Tailscale Funnel
---

# 目標

依照老師的 HackMD 投影片，在 Windows PC 上執行 Docker Compose、n8n、LINE gateway 和 Tailscale Funnel，讓老師加 LINE 官方帳號好友後可用繁體中文文字聊天。Bonus 是短期記憶；本版遵循投影片的 stateless 設計，每則訊息獨立處理，不記住先前內容。

## 架構

```text
LINE Messaging API
  │ HTTPS POST /line/webhook
  ▼
Tailscale Funnel ──▶ gateway（驗證 X-Line-Signature）
                          │ POST 事件
                          ▼
                     n8n workflow
                     ├─ 篩選文字事件、去重
                     ├─ 呼叫 Gemini
                     └─ 用 LINE Reply API 回覆
```

- `n8n` 管理聊天 workflow，只綁定本機 `127.0.0.1:5678`。
- `gateway` 對內提供 `8080`，經 Tailscale Funnel 取得公開 HTTPS 網址。
- `workflow-init` 首次啟動時將 `workflows/linebot-workflow.json` 匯入 n8n，之後由 n8n UI 管理。
- gateway 驗證 LINE 簽章後才轉送事件；只處理文字，貼圖、圖片、影片、語音會忽略。
- workflow 不保存成功或失敗執行內容；短期記憶不包含在這份 stateless workflow。

## 需要的本機憑證

`.env` 需包含 LINE `CHANNEL_SECRET`、`CHANNEL_ACCESS_TOKEN`、Google `GEMINI_API_KEY`、`GEMINI_MODEL`，以及 n8n `N8N_ENCRYPTION_KEY`。`scripts/configure.ps1` 會安全地產生 n8n 加密金鑰，不會顯示金鑰值。Tailscale 裝置登入由使用者在瀏覽器自行授權；不需要建立 auth key。

## Windows 啟動

1. 啟動 Docker Desktop，等待 Linux engine 就緒；用一般 PowerShell 執行 `docker info --format '{{.OSType}}/{{.Architecture}}'`，應顯示 `linux/x86_64`（或相容的 Linux 架構）。
2. 第一次設定 n8n 本機加密金鑰：

   ```powershell
   .\scripts\configure.ps1
   ```

3. 在 `.env` 確認 LINE/Gemini 憑證已填妥；Tailscale 以互動式登入加入 tailnet。不要輸出或分享 `.env`。
4. 啟動服務：

   ```powershell
   docker compose up -d --build
   docker compose ps -a
   ```

5. `workflow-init` 應為 `Exited (0)`，`n8n` 與 `gateway` 應為 `healthy`，`tailscale` 應為 `Up`。開啟 `http://localhost:5678`，建立本機管理帳號，找到 `LINE stateless text chatbot` 並確認已發布。
6. 啟用 Funnel 並取得公開網址：

   ```powershell
   .\scripts\connect-tailscale.ps1
   # 在瀏覽器開啟 PowerShell 顯示的登入連結並授權
   docker compose exec tailscale tailscale status
   docker compose exec tailscale tailscale funnel --bg http://127.0.0.1:8080
   docker compose exec tailscale tailscale funnel status
   ```

   用 `https://你的裝置.你的-tailnet.ts.net/healthz` 確認公開入口回傳 `{"ok":true}`。
7. 在 LINE Developers 的 Messaging API 頁設定 `https://你的 Funnel 網址/line/webhook`，按 Update、Verify 成功後開啟 Use webhook。Official Account Manager 的自動回應與歡迎訊息維持關閉。
8. 用 LINE 傳「你好」測試繁體中文回覆；再分兩則傳「我叫小明」和「我叫什麼名字？」，stateless 設計預期不會記得先前訊息。

## 停止與資料

- `docker compose down` 停止容器並保留 n8n 與 Tailscale volumes。
- 不要執行 `docker compose down -v`，除非明確要刪除 n8n 工作流程／本機帳號與 Tailscale 狀態。
- `.env`、LINE webhook payload、Gemini prompt 與回覆不得提交 Git。workflow 設定不保存執行歷程。

## 驗收與貢獻

- `python -m compileall -q gateway/app.py`
- `docker compose config --quiet`
- `docker compose ps -a` 狀態符合上方預期。
- LINE Developers Verify 成功，好友傳文字可收到回覆；簽章錯誤必須被拒絕。
- 修改設定後更新 README，檢查 `git status` 與 `git diff`；不得提交秘密、`.env`、cache、volume 或 scratch 檔案。

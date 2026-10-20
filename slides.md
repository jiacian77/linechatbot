---
title: 用自己的 PC 打造 LINE 聊天機器人
subtitle: Docker Compose、n8n、Gemini 與 Tailscale Funnel
---

# 用自己的 PC
# 打造 LINE 聊天機器人

### LINE Messaging API × n8n × Gemini

本機容器執行流程，透過 Tailscale Funnel 讓老師加好友聊天

---

## 今天要完成什麼？

1. 在自己的 PC 上跑 LINE 聊天機器人
2. 加老師為好友，並能順利聊天
3. Bonus：理解 stateless 對話與短期記憶的差異

---

## 訊息如何到達 bot？

```text
老師的 LINE
  → LINE Messaging API
  → Tailscale Funnel 公開 HTTPS
  → Gateway 驗證 LINE 簽章
  → n8n workflow 篩選文字
  → Gemini 產生回答
  → LINE Reply API
  → 老師收到回覆
```

Gateway 是唯一公開入口；n8n 編輯介面只在本機開啟。

---

## 準備工具與憑證

- Windows 11 PC、WSL 2、Docker Desktop、Git for Windows
- LINE Messaging API：Channel access token、Channel secret
- Google AI Studio：Gemini API key
- Tailscale 帳號（裝置以互動式登入授權，不需 auth key）
- 憑證保存在本機 `.env`，不要貼在聊天或提交 GitHub

---

## 啟動 Docker 環境

PowerShell 確認 Docker Desktop 已啟動：

```powershell
docker version
docker compose version
docker info --format '{{.OSType}}/{{.Architecture}}'
docker run --rm hello-world
```

預期引擎為 Linux，hello-world 顯示成功訊息。

---

## 設定本機憑證

1. 在 LINE Developers 建立 Messaging API channel，取得 Secret 並簽發 access token
2. 在 Google AI Studio 建立 Gemini API key
3. 啟動 Tailscale 容器並依 CLI 顯示的連結授權裝置
4. 在 repository 的 `.env` 設定必要憑證
5. 執行 `./scripts/configure.ps1` 建立 n8n 加密金鑰

`.env` 不可提交到 Git。不要把完整 webhook payload 寫進日誌。

---

## 啟動 n8n、Gateway、Tailscale

```powershell
docker compose up -d --build
docker compose ps -a
```

預期：`workflow-init` 為 `Exited (0)`；`n8n`、`gateway` 為 `healthy`；`tailscale` 為 `Up`。

---

## 開啟 n8n workflow

1. 開啟 `http://localhost:5678`
2. 建立本機 n8n 管理帳號
3. 找到 `LINE stateless text chatbot`
4. 確認 workflow 已發布

Webhook 節點由內部 gateway 呼叫；不要將 n8n 管理介面公開到網際網路。

---

## 啟用 Tailscale Funnel

```powershell
docker compose exec tailscale tailscale status
docker compose exec tailscale tailscale funnel --bg http://127.0.0.1:8080
docker compose exec tailscale tailscale funnel status
```

執行 `./scripts/connect-tailscale.ps1`，在瀏覽器開啟終端機顯示的登入網址並確認裝置加入；完成後再啟用 Funnel，記下 HTTPS 網址。

---

## 設定 LINE Webhook

在 LINE Developers 的 Messaging API 頁面：

1. Webhook URL 填入 `https://你的-funnel-網址/line/webhook`
2. 按 Update，再按 Verify，確認 Success
3. 開啟 Use webhook
4. 在官方帳號後台關閉自動回應與歡迎訊息

先用 `https://你的-funnel-網址/healthz` 確認回傳 `{"ok":true}`。

---

## 加好友並測試

1. 從官方帳號管理頁複製好友連結或 QR code
2. 老師加好友後傳送「你好」
3. 確認 bot 回覆繁體中文
4. 文字訊息會處理；貼圖、圖片、影片與語音會忽略

---

## Bonus：短期記憶與 stateless

老師投影片的首版 workflow 採 stateless：每次只處理當次文字，所以不記住前次訊息。

可以用「我叫小明」再問「我叫什麼名字？」驗證。預期 bot 不引用前一則訊息。

若要增加短期記憶，需要另外設計依 LINE user ID 分區、有期限與清除方式的儲存層，再更新 workflow。

---

## 驗收與常見問題

- `docker compose ps -a` 顯示服務健康
- `/healthz` 回傳 `{"ok":true}`
- LINE Developers Verify 成功
- 好友傳文字能收到 Gemini 回覆
- Verify 失敗：檢查 Funnel、Channel Secret 與 URL 的 `/line/webhook`
- 沒有回覆：查看 n8n Executions 與 `docker compose logs gateway n8n`

---

## 隱私與停止服務

- 成功與失敗的 n8n 執行資料不保存
- `.env` 和使用者訊息不可提交或分享
- `docker compose down` 停止服務並保留 volumes
- `docker compose down -v` 會刪除 n8n/Tailscale 資料，謹慎使用

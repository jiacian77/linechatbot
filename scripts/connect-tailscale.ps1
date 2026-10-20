$ErrorActionPreference = 'Continue'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repoRoot
$docker = 'C:\Users\user\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe'
Write-Host '正在向 Tailscale 取得登入連結…'
& $docker compose exec tailscale tailscale up --hostname=linebot --accept-dns=false
Write-Host ''
Write-Host '請在上方找到 Tailscale 登入連結，於瀏覽器開啟並確認裝置加入。'
Read-Host '授權完成後按 Enter 關閉此視窗'

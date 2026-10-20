$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$envPath = Join-Path $repoRoot '.env'
$examplePath = Join-Path $repoRoot '.env.example'

if (-not (Test-Path -LiteralPath $envPath)) {
    Copy-Item -LiteralPath $examplePath -Destination $envPath
    Write-Host '已建立 .env。請填入 LINE 與 Gemini 憑證後再重新執行此腳本。'
    exit 0
}

$lines = @(Get-Content -LiteralPath $envPath)
$keyName = 'N8N_ENCRYPTION_KEY'
$keyPattern = '^N8N_ENCRYPTION_KEY='
$existing = $lines | Where-Object { $_ -match $keyPattern } | Select-Object -First 1

if (-not $existing -or $existing -match '^N8N_ENCRYPTION_KEY\s*=\s*$') {
    $bytes = [byte[]]::new(32)
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    $generatedKey = [Convert]::ToBase64String($bytes)
    $replacement = "N8N_ENCRYPTION_KEY=$generatedKey"
    if ($existing) {
        $lines = @($lines | ForEach-Object { if ($_ -match $keyPattern) { $replacement } else { $_ } })
    } else {
        $lines += $replacement
    }
    Set-Content -LiteralPath $envPath -Value $lines -Encoding utf8
    Write-Host '已在本機 .env 建立 n8n 加密金鑰。'
} else {
    Write-Host 'n8n 加密金鑰已設定。'
}

Write-Host '設定完成；LINE 與 Gemini 憑證只保存在本機 .env。Tailscale 使用互動式登入，不需 auth key。'

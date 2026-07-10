$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Write-Status([string]$Message) {
    $stamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$stamp] $Message"
}

function Stop-PublicStack {
    Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    Get-Process cloudflared, node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
}

function Ensure-Cloudflared {
    $cf = Join-Path $Root "tools\cloudflared.exe"
    if (Test-Path $cf) { return $cf }

    New-Item -ItemType Directory -Force -Path (Join-Path $Root "tools") | Out-Null
    Write-Status "cloudflared 다운로드 중..."
    Invoke-WebRequest `
        -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" `
        -OutFile $cf
    return $cf
}

function Wait-LocalHealth {
    for ($i = 0; $i -lt 40; $i++) {
        try {
            $res = Invoke-WebRequest "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 2
            if ($res.StatusCode -eq 200) { return $true }
        } catch {}
        Start-Sleep -Seconds 1
    }
    return $false
}

function Wait-PublicHealth([string]$Url) {
    Start-Sleep -Seconds 5
    for ($i = 0; $i -lt 40; $i++) {
        try {
            $res = curl.exe -sS -m 8 -w "%{http_code}" "$Url/health"
            if ($res -match "200$") { return $true }
        } catch {}
        Start-Sleep -Seconds 2
    }
    return $false
}

function Read-TunnelUrl([string]$LogPath, [string]$ErrPath) {
    $logParts = @()
    if (Test-Path $LogPath) { $logParts += Get-Content $LogPath -Raw -ErrorAction SilentlyContinue }
    if (Test-Path $ErrPath) { $logParts += Get-Content $ErrPath -Raw -ErrorAction SilentlyContinue }
    $log = ($logParts -join "`n")
    if ($log -match "(https://[a-z0-9-]+\.trycloudflare\.com)") { return $matches[1] }
    if ($log -match "(https://[a-z0-9-]+\.loca\.lt)") { return $matches[1] }
    return $null
}

function Start-CloudflaredTunnel([string]$CfPath, [string]$LogPath, [string]$ErrPath) {
    if (Test-Path $LogPath) { Remove-Item $LogPath -Force }
    if (Test-Path $ErrPath) { Remove-Item $ErrPath -Force }
    Start-Process $CfPath `
        -ArgumentList @("tunnel", "--url", "http://127.0.0.1:8000") `
        -WorkingDirectory $Root `
        -WindowStyle Hidden `
        -RedirectStandardOutput $LogPath `
        -RedirectStandardError $ErrPath | Out-Null
    for ($i = 0; $i -lt 45; $i++) {
        $url = Read-TunnelUrl $LogPath $ErrPath
        if ($url) { return $url }
        Start-Sleep -Seconds 1
    }
    return $null
}

function Start-Localtunnel {
    $ltLog = Join-Path $Root "logs\localtunnel.log"
    $ltErr = Join-Path $Root "logs\localtunnel.err.log"
    if (Test-Path $ltLog) { Remove-Item $ltLog -Force }
    if (Test-Path $ltErr) { Remove-Item $ltErr -Force }
    Write-Status "localtunnel 백업 터널 시도"
    Start-Process npx `
        -ArgumentList @("--yes", "localtunnel", "--port", "8000") `
        -WorkingDirectory $Root `
        -WindowStyle Hidden `
        -RedirectStandardOutput $ltLog `
        -RedirectStandardError $ltErr | Out-Null
    for ($i = 0; $i -lt 60; $i++) {
        $url = Read-TunnelUrl $ltLog $ltErr
        if ($url) { return $url }
        Start-Sleep -Seconds 1
    }
    return $null
}

Write-Status "기존 서버/터널 정리"
Stop-PublicStack
Start-Sleep -Seconds 2

New-Item -ItemType Directory -Force -Path (Join-Path $Root "logs") | Out-Null
$uvicornLog = Join-Path $Root "logs\uvicorn.log"
$cfLog = Join-Path $Root "logs\cloudflared.log"
$cfErrLog = Join-Path $Root "logs\cloudflared.err.log"

Write-Status "로컬 서버 시작 (127.0.0.1:8000)"
Start-Process python `
    -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000") `
    -WorkingDirectory $Root `
    -WindowStyle Hidden `
    -RedirectStandardOutput $uvicornLog `
    -RedirectStandardError (Join-Path $Root "logs\uvicorn.err.log") | Out-Null

if (-not (Wait-LocalHealth)) {
    throw "로컬 서버가 시작되지 않았습니다. logs/uvicorn.log 를 확인하세요."
}
Write-Status "로컬 서버 정상"

$cf = Ensure-Cloudflared
Write-Status "Cloudflare 터널 시작"
$publicUrl = Start-CloudflaredTunnel $cf $cfLog $cfErrLog

if (-not $publicUrl) {
    $publicUrl = Start-Localtunnel
}

if (-not $publicUrl) {
    throw "공개 URL을 가져오지 못했습니다. logs/cloudflared.err.log 또는 logs/localtunnel.err.log 를 확인하세요."
}

if (-not (Wait-PublicHealth $publicUrl)) {
    throw "공개 URL이 아직 응답하지 않습니다: $publicUrl"
}

$shareObj = [ordered]@{
    public_url = $publicUrl
    app = "$publicUrl/"
    home = "$publicUrl/home"
    chat = "$publicUrl/chat"
    tarot = "$publicUrl/tarot"
    test = "$publicUrl/test"
    legal = "$publicUrl/legal"
    health = "$publicUrl/health"
    started_at = (Get-Date).ToUniversalTime().ToString("o")
}
($shareObj | ConvertTo-Json -Depth 3) | Set-Content (Join-Path $Root "public-url.json") -Encoding UTF8

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " 공개 배포 완료" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "앱   : $($shareObj.app)"
Write-Host "홈   : $($shareObj.home)"
Write-Host "대화 : $($shareObj.chat)"
Write-Host "타로 : $($shareObj.tarot)"
Write-Host "법률 : $($shareObj.legal)"
Write-Host "테스트: $($shareObj.test)"
Write-Host ""
Write-Host "링크는 public-url.json 에 저장되었습니다."
Write-Host "이 PC가 켜져 있고 터널 프로세스가 살아 있어야 접속됩니다."
Write-Host "영구 URL: https://render.com/deploy?repo=https://github.com/jayhope9907/psychology-tarot-ai"

$Root = Split-Path -Parent $PSScriptRoot

Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

$publicFile = Join-Path $Root "public-url.json"
if (Test-Path $publicFile) { Remove-Item $publicFile -Force }

Write-Host "공개 서버/터널을 종료했습니다."

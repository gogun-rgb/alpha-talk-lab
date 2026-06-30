$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"

function Test-PortInUse([int]$Port) {
  $Client = New-Object System.Net.Sockets.TcpClient
  try {
    $Client.Connect("127.0.0.1", $Port)
    return $true
  }
  catch {
    return $false
  }
  finally {
    $Client.Close()
  }
}

if (Test-PortInUse 8000) { throw "8000 포트가 이미 사용 중입니다." }
if (Test-PortInUse 3000) { throw "3000 포트가 이미 사용 중입니다." }
if (-not (Test-Path -LiteralPath $VenvPython)) { throw ".venv가 없습니다. scripts/setup.ps1을 먼저 실행해 주세요." }

Write-Host "FastAPI: http://localhost:8000"
Write-Host "Next.js: http://localhost:3000"

Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "Set-Location '$Backend'; & '$VenvPython' -m uvicorn app.main:app --reload --port 8000"
)

Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "Set-Location '$Frontend'; `$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:8000'; pnpm dev"
)

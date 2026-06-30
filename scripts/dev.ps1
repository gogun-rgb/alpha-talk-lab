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

function Get-FreePort([int[]]$Ports, [string]$Name) {
  foreach ($Port in $Ports) {
    if (-not (Test-PortInUse $Port)) {
      return $Port
    }
  }
  throw "$Name 포트를 찾지 못했습니다. 후보: $($Ports -join ', ')"
}

$BackendPort = Get-FreePort @(8000, 8001, 8002) "FastAPI"
$FrontendPort = Get-FreePort @(3000, 3001, 3002) "Next.js"
if (-not (Test-Path -LiteralPath $VenvPython)) { throw ".venv가 없습니다. scripts/setup.ps1을 먼저 실행해 주세요." }

Write-Host "FastAPI: http://localhost:$BackendPort"
Write-Host "Next.js: http://localhost:$FrontendPort"

Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "Set-Location '$Backend'; & '$VenvPython' -m uvicorn app.main:app --reload --port $BackendPort"
)

Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "Set-Location '$Frontend'; `$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:$BackendPort'; pnpm exec next dev --port $FrontendPort"
)

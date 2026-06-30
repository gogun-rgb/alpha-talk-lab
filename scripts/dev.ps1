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

function Get-PortOwner([int]$Port) {
  $Connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $Connection) {
    return $null
  }
  return Get-CimInstance Win32_Process -Filter "ProcessId = $($Connection.OwningProcess)" -ErrorAction SilentlyContinue
}

function Test-CurrentProjectProcess($Process, [string]$ExpectedPath) {
  if (-not $Process -or -not $Process.CommandLine) {
    return $false
  }
  return $Process.CommandLine -like "*$ExpectedPath*"
}

function Get-FreePort([int[]]$Ports, [string]$Name) {
  foreach ($Port in $Ports) {
    if (-not (Test-PortInUse $Port)) {
      return $Port
    }
    $Owner = Get-PortOwner $Port
    if ($Owner) {
      $Kind = if (Test-CurrentProjectProcess $Owner $Root) { "현재 AlphaTalk Lab 프로세스" } else { "다른 프로세스" }
      Write-Host "$Name 후보 포트 $Port 사용 중: $Kind (PID $($Owner.ProcessId))"
    }
  }
  throw "$Name 포트를 찾지 못했습니다. 후보: $($Ports -join ', ')"
}

function Wait-BackendHealth([int]$Port) {
  $HealthUrl = "http://localhost:$Port/health"
  for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
    try {
      $Response = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 2
      if ($Response.StatusCode -eq 200) {
        return
      }
    }
    catch {
      Start-Sleep -Milliseconds 500
    }
  }
  throw "FastAPI가 $HealthUrl 에서 응답하지 않습니다."
}

$BackendPort = Get-FreePort @(8000, 8001, 8002) "FastAPI"
$FrontendPort = Get-FreePort @(3000, 3001, 3002) "Next.js"
if (-not (Test-Path -LiteralPath $VenvPython)) { throw ".venv가 없습니다. scripts/setup.ps1을 먼저 실행해 주세요." }

$FrontendOrigins = "http://localhost:$FrontendPort,http://127.0.0.1:$FrontendPort"
Write-Host "Selected FastAPI API: http://localhost:$BackendPort"
Write-Host "Selected Next.js app: http://localhost:$FrontendPort"
Write-Host "Backend CORS origins: $FrontendOrigins"

Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "Set-Location '$Backend'; `$env:FRONTEND_ORIGINS='$FrontendOrigins'; & '$VenvPython' -m uvicorn app.main:app --reload --port $BackendPort"
)

Wait-BackendHealth $BackendPort
Write-Host "FastAPI health OK: http://localhost:$BackendPort/health"

Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "Set-Location '$Frontend'; `$env:NEXT_PUBLIC_API_BASE_URL='http://localhost:$BackendPort'; pnpm exec next dev --port $FrontendPort"
)

Write-Host "Open: http://localhost:$FrontendPort"
Write-Host "Frontend API target: http://localhost:$BackendPort"

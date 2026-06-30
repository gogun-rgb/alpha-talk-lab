$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $VenvPython)) { throw ".venv가 없습니다. scripts/setup.ps1을 먼저 실행해 주세요." }

Push-Location $Backend
try {
  & $VenvPython -m pytest
}
finally {
  Pop-Location
}

Push-Location $Frontend
try {
  pnpm lint
  pnpm typecheck
  pnpm test
  pnpm build
}
finally {
  Pop-Location
}

Write-Host "모든 검증 명령이 통과했습니다."

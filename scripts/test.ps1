$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

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

Write-Host "All verification commands passed."

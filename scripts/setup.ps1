$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$Venv = Join-Path $Root ".venv"
$Python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $Python) {
  $Python = (Get-Command py -ErrorAction SilentlyContinue).Source
}
if (-not $Python) {
  throw "Python을 찾지 못했습니다. Python 3.11 이상을 설치해 주세요."
}

if (-not (Test-Path -LiteralPath $Venv)) {
  & $Python -m venv $Venv
}

$VenvPython = Join-Path $Venv "Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r (Join-Path $Backend "requirements.txt")

Push-Location $Frontend
try {
  if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    throw "pnpm을 찾지 못했습니다. Node.js와 pnpm을 설치해 주세요."
  }
  pnpm install
}
finally {
  Pop-Location
}

$EnvFile = Join-Path $Root ".env"
if (-not (Test-Path -LiteralPath $EnvFile)) {
  Write-Host ".env 파일이 없습니다. .env.example을 복사한 뒤 필요한 값을 입력해 주세요."
  Write-Host "Copy-Item .env.example .env"
}

Write-Host "설치가 완료되었습니다."

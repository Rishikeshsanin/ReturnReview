param([switch]$Build)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".env.demo")) {
  Write-Host "Presentation configuration is missing." -ForegroundColor Yellow
  Write-Host "Copy your EXISTING private config from the original working project:" -ForegroundColor Yellow
  Write-Host 'Copy-Item "F:\Projects\ReturnReview\.env.demo" ".\.env.demo"'
  Write-Host "Never commit or share .env.demo."
  exit 2
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Write-Error "Docker command not found. Open Docker Desktop."
  exit 1
}
docker info *> $null
if ($LASTEXITCODE -ne 0) {
  Write-Error "Docker Engine is not running. Open Docker Desktop."
  exit 1
}
$command = @("compose","--env-file",".env.demo","-f","compose.presentation.yml","up","-d")
if ($Build) { $command += "--build" }
& docker @command
if ($LASTEXITCODE -ne 0) {
  Write-Error "Presentation containers failed. Check compose logs."
  exit 1
}
Write-Host "Presentation UI: http://localhost:3100" -ForegroundColor Green
Write-Host "Presentation API: http://localhost:8100/readiness" -ForegroundColor Cyan
Write-Host "Original UI (if running): http://localhost:3000" -ForegroundColor DarkGray
Write-Host "To stop ONLY the presentation: docker compose --env-file .env.demo -f compose.presentation.yml stop"

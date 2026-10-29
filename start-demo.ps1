$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is unavailable. Install/start Docker Desktop, then rerun this script."
    exit 1
}

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker Desktop engine is not running. Start Docker Desktop and rerun."
    exit 1
}

if (-not (Test-Path ".env.demo")) {
    Copy-Item "demo-config.example" ".env.demo"
    Write-Host "Created .env.demo. Edit it first: set a unique local DB password and (for Gemini) a valid API key, then set RETURNREVIEW_LLM_ENABLED=true." -ForegroundColor Yellow
    Write-Host "Open the file with: notepad .env.demo"
    exit 2
}

Write-Host "Starting ReturnReview from existing Dockerfiles and verified CV release..."
docker compose --env-file .env.demo -f compose.demo.yml up -d --build
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker build/start failed. Run: docker compose --env-file .env.demo -f compose.demo.yml logs --tail=100"
    exit 1
}

Write-Host "ReturnReview containers started. Checking API..." -ForegroundColor Green
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 10
    $ready = Invoke-RestMethod -Uri "http://localhost:8000/readiness" -TimeoutSec 15
    Write-Host ("Health: " + ($health | ConvertTo-Json -Compress))
    Write-Host ("Readiness: " + ($ready | ConvertTo-Json -Compress))
} catch {
    Write-Warning "The API may still be starting; inspect logs before the demo."
}
Write-Host "Web UI: http://localhost:3000" -ForegroundColor Green
Write-Host "API: http://localhost:8000; readiness: http://localhost:8000/readiness"
Write-Host "Stop containers (preserves Postgres data): docker compose --env-file .env.demo -f compose.demo.yml down"

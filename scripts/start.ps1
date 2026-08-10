param([switch]$CheckOnly)

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $projectRoot '.run'
$logDir = Join-Path $runtimeDir 'logs'
$envFile = Join-Path $projectRoot '.env'
$envExample = Join-Path $projectRoot '.env.example'

function Test-HttpEndpoint {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 400
    }
    catch {
        return $false
    }
}

function Wait-ForEndpoint {
    param(
        [string]$Name,
        [string]$Url,
        [int]$Attempts = 40
    )
    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        if (Test-HttpEndpoint $Url) {
            Write-Host "[OK] $Name is ready" -ForegroundColor Green
            return $true
        }
        Start-Sleep -Milliseconds 500
    }
    Write-Host "[FAILED] $Name did not start in time" -ForegroundColor Red
    return $false
}

Set-Location $projectRoot
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

Write-Host 'Kline Melody launcher' -ForegroundColor Cyan
Write-Host '----------------'

if (-not (Test-Path $envFile)) {
    Copy-Item -LiteralPath $envExample -Destination $envFile
    Write-Host '[CONFIG REQUIRED] Created .env. Set MYSQL_PASSWORD and run again.' -ForegroundColor Yellow
    exit 1
}

$passwordLine = Get-Content -LiteralPath $envFile | Where-Object { $_ -match '^MYSQL_PASSWORD=' } | Select-Object -First 1
if (-not $passwordLine -or $passwordLine -match '^MYSQL_PASSWORD=(|replace-with-local-password)$') {
    Write-Host '[CONFIG REQUIRED] Set MYSQL_PASSWORD in .env first.' -ForegroundColor Yellow
    exit 1
}

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
$nodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
$npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $pythonCommand) { throw 'Python was not found. Install Python 3.11 or newer.' }
if (-not $nodeCommand -or -not $npmCommand) { throw 'Node.js/npm was not found. Install Node.js first.' }

$pythonExecutable = & $pythonCommand.Source -c "import sys; print(sys.executable)"
if (-not $pythonExecutable) { throw 'Could not resolve the Python executable.' }

& $pythonExecutable -c "import fastapi, uvicorn, sqlalchemy, pymysql" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host '[SETUP] Installing backend dependencies...' -ForegroundColor Yellow
    & $pythonExecutable -m pip install -r (Join-Path $projectRoot 'backend\requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Backend dependency installation failed.' }
}

$viteScript = Join-Path $projectRoot 'node_modules\vite\bin\vite.js'
if (-not (Test-Path $viteScript)) {
    Write-Host '[SETUP] Installing frontend dependencies...' -ForegroundColor Yellow
    & $npmCommand.Source install
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
}

if ($CheckOnly) {
    Write-Host '[OK] Configuration and dependencies are ready. Services were not started.' -ForegroundColor Green
    exit 0
}

$backendUrl = 'http://127.0.0.1:8000/api/health'
$frontendUrl = 'http://127.0.0.1:5173/'

if (Test-HttpEndpoint $backendUrl) {
    Write-Host '[SKIP] Backend is already running' -ForegroundColor DarkYellow
}
else {
    $backendProcess = Start-Process -FilePath $pythonExecutable -ArgumentList @(
        '-m', 'uvicorn', 'backend.app.main:app', '--host', '127.0.0.1', '--port', '8000',
        '--reload', '--reload-dir', 'backend'
    ) -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logDir 'backend.out.log') -RedirectStandardError (Join-Path $logDir 'backend.err.log') -PassThru
    Set-Content -LiteralPath (Join-Path $runtimeDir 'backend.pid') -Value $backendProcess.Id
}

if (Test-HttpEndpoint $frontendUrl) {
    Write-Host '[SKIP] Frontend is already running' -ForegroundColor DarkYellow
}
else {
    $frontendProcess = Start-Process -FilePath $nodeCommand.Source -ArgumentList @(
        $viteScript, '--host', '127.0.0.1', '--port', '5173'
    ) -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logDir 'frontend.out.log') -RedirectStandardError (Join-Path $logDir 'frontend.err.log') -PassThru
    Set-Content -LiteralPath (Join-Path $runtimeDir 'frontend.pid') -Value $frontendProcess.Id
}

$backendReady = Wait-ForEndpoint -Name 'FastAPI backend' -Url $backendUrl
$frontendReady = Wait-ForEndpoint -Name 'Vite frontend' -Url $frontendUrl

if (-not $backendReady -or -not $frontendReady) {
    Write-Host "Check logs at: $logDir" -ForegroundColor Yellow
    exit 1
}

Write-Host ''
Write-Host "Frontend: $frontendUrl" -ForegroundColor Cyan
Write-Host 'API docs: http://127.0.0.1:8000/docs' -ForegroundColor Cyan
Write-Host "Logs: $logDir" -ForegroundColor DarkGray
Start-Process $frontendUrl

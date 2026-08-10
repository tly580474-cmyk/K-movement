$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $projectRoot '.run'

function Stop-TrackedProcess {
    param(
        [string]$Name,
        [string]$PidFile,
        [string]$ExpectedCommand
    )
    if (-not (Test-Path $PidFile)) {
        Write-Host "[SKIP] No process record for $Name"
        return
    }

    $processId = [int](Get-Content -LiteralPath $PidFile | Select-Object -First 1)
    $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $processId" -ErrorAction SilentlyContinue
    if (-not $processInfo) {
        Write-Host "[SKIP] $Name is already stopped"
        Remove-Item -LiteralPath $PidFile -Force
        return
    }
    if ($processInfo.CommandLine -notlike "*$ExpectedCommand*") {
        Write-Host "[SAFEGUARD] PID $processId belongs to another command and was not stopped." -ForegroundColor Yellow
        Remove-Item -LiteralPath $PidFile -Force
        return
    }

    Stop-Process -Id $processId
    Remove-Item -LiteralPath $PidFile -Force
    Write-Host "[OK] $Name stopped" -ForegroundColor Green
}

Write-Host 'Stopping Kline Melody...' -ForegroundColor Cyan
Stop-TrackedProcess -Name 'Vite frontend' -PidFile (Join-Path $runtimeDir 'frontend.pid') -ExpectedCommand 'vite.js'
Stop-TrackedProcess -Name 'FastAPI backend' -PidFile (Join-Path $runtimeDir 'backend.pid') -ExpectedCommand 'uvicorn'

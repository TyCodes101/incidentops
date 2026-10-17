param([switch]$Demo)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$pythonPath = Join-Path (Get-Location) '.venv/Scripts/python.exe'
if (!(Test-Path -LiteralPath $pythonPath)) { throw 'Create .venv and install .[dev] first. See README.' }
$env:APP_ORIGIN = 'http://localhost:5173'
if ($env:APP_ENV -eq 'production') { throw 'Development launcher cannot run in production.' }
& $pythonPath -m alembic upgrade head
if ($LASTEXITCODE) { throw 'Migration failed' }
if ($Demo) { & $pythonPath -m incidentops.manage demo; if ($LASTEXITCODE) { throw 'Demo seed failed' } }
Push-Location frontend
try { npm.cmd ci; if ($LASTEXITCODE) { throw 'Frontend dependency installation failed' } } finally { Pop-Location }
New-Item -ItemType Directory -Force .runtime | Out-Null
$apiProcess = Start-Process -FilePath $pythonPath -ArgumentList @('-m','uvicorn','incidentops.main:app','--host','127.0.0.1','--port','8000') -PassThru -WindowStyle Hidden -RedirectStandardOutput '.runtime/api.log' -RedirectStandardError '.runtime/api-error.log'
try {
    Write-Host 'Open http://localhost:5173. Press Ctrl+C to stop both services.'
    Push-Location frontend
    try { npm.cmd run dev } finally { Pop-Location }
} finally { if (!$apiProcess.HasExited) { Stop-Process -Id $apiProcess.Id } }

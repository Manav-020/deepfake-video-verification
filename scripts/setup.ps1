$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path .venv\Scripts\python.exe)) {
    py -3.13 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.13 from python.org first.' }
}
$python = Join-Path (Get-Location) '.venv\Scripts\python.exe'
& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip update failed' }
& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Application dependency installation failed' }
& $python -m pip install -r requirements-cpu.txt
if ($LASTEXITCODE -ne 0) { throw 'CPU torch installation failed' }
& $python scripts\setup_faces.py
if ($LASTEXITCODE -ne 0) { throw 'MTCNN weights installation failed' }
& $python scripts\download_model.py
if ($LASTEXITCODE -ne 0) { throw 'Model download failed; app will fail closed until corrected' }
Write-Host 'Setup finished. Run .\scripts\run.ps1'
New-Item -ItemType Directory -Force datasets\validation\real,datasets\validation\fake,datasets\test\real,datasets\test\fake | Out-Null

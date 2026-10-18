$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path .venv\Scripts\python.exe)) { throw 'Run .\scripts\setup.ps1 first' }
& .\.venv\Scripts\python.exe -m uvicorn app.asgi:app --host 127.0.0.1 --port 8000 --workers 1

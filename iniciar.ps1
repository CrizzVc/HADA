Set-Location $PSScriptRoot
if (Test-Path ".\.venv\Scripts\python.exe") {
    & ".\.venv\Scripts\python.exe" main.py
} else {
    Write-Host "[!] Activando entorno virtual..." -ForegroundColor Yellow
    .\.venv\Scripts\activate
    python main.py
}


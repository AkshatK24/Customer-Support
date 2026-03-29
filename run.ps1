# Run Script for Customer Support Environment
# Usage: .\run.ps1

Write-Host "STARTING: Customer Support Environment" -ForegroundColor Cyan

# 1. Clean up ports
Write-Host "Cleaning up ports 7860/7861..." -ForegroundColor Gray
$ports = 7860, 7861
foreach ($port in $ports) {
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn.OwningProcess) {
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

# 2. Check for .venv
if (!(Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Gray
    python -m venv .venv
}

# 3. Start the server
Write-Host "Server running at http://localhost:7860" -ForegroundColor Green
Write-Host "(Press Ctrl+C to stop)" -ForegroundColor White
.\.venv\Scripts\python.exe -m uvicorn server.app:app --host 0.0.0.0 --port 7860

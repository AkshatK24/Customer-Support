# Run Script for Customer Support Environment
# Usage: .\run.ps1 <command>
# Commands: (none) - Start server
#           test   - Run automated test suite

param([string]$command = "")

Write-Host "STARTING: Customer Support Environment" -ForegroundColor Cyan

# 1. Clean up ports
Write-Host "Cleaning up ports 7860/7861..." -ForegroundColor Gray
$ports = 7860, 7861
foreach ($port in $ports) {
    try {
        $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if ($conn.OwningProcess) {
            Write-Host "   Stopping process on port $port..." -ForegroundColor Yellow
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    } catch {}
}

# 2. Check for .venv
if (!(Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Gray
    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -e .
    .\.venv\Scripts\python.exe -m pip install pytest httpx
}

# 3. Handle commands
if ($command -eq "test") {
    Write-Host "Running Automated Test Suite..." -ForegroundColor Green
    .\.venv\Scripts\python.exe -m pytest tests/ -v
    exit
}

# Default: Start the server
Write-Host "Server running at http://localhost:7860" -ForegroundColor Green
Write-Host "(Press Ctrl+C to stop)" -ForegroundColor White
.\.venv\Scripts\python.exe -m uvicorn server.app:app --host 0.0.0.0 --port 7860

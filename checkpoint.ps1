param([string]$Message = "Milestone update")

Write-Host "`n>>> RUNNING AUTO-CHECKPOINT PIPELINE..." -ForegroundColor Cyan

# 1. Update requirements.txt if virtual environment is present
if (Test-Path ".\.venv\Scripts\pip.exe") {
    & ".\.venv\Scripts\pip.exe" freeze > requirements.txt
    Write-Host "[OK] requirements.txt synchronized." -ForegroundColor Green
}

# 2. Safety check: Ensure .env is never staged
git status --porcelain | ForEach-Object {
    if ($_ -match "\.env$") {
        Write-Host "[CRITICAL ERROR] .env file detected in git staging! Aborting commit." -ForegroundColor Red
        exit 1
    }
}

# 3. Stage, commit, and push
git add .
git commit -m $Message
git push origin main

Write-Host ">>> [SUCCESS] Checkpoint pushed to GitHub: $Message" -ForegroundColor Green
Write-Host ">>> View at: https://github.com/parthbhaskar/jarvis-vision`n" -ForegroundColor Yellow

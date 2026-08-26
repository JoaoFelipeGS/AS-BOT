# Start the full AS Marketplace Bot SaaS stack on Windows.
# Usage: Open PowerShell in the repository root and run: .\start-app.ps1

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

Write-Host "Repository root: $repoRoot"

# Create virtual environment if missing
if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv .venv
}

Write-Host "Activating virtual environment..."
. .\.venv\Scripts\Activate.ps1

Write-Host "Upgrading pip and installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# Ensure pydantic-settings is installed for current backend configuration
pip install pydantic-settings

# Ensure playwright is installed and browsers are available
pip install playwright
playwright install chromium

# Load environment variables from .env so child windows inherit them
if (Test-Path ".env") {
    Write-Host "Loading .env variables..."
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*([^#=\s][^=]*)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim(' "')
            Set-Item -Path env:$name -Value $value
        }
    }
}

$backendCommand = ". .\.venv\Scripts\Activate.ps1; python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
$frontendCommand = "cd frontend; npm run dev"

Write-Host "Starting backend in a new PowerShell window..."
Start-Process powershell -ArgumentList '-NoExit', '-Command', $backendCommand

Write-Host "Starting frontend in a new PowerShell window..."
Start-Process powershell -ArgumentList '-NoExit', '-Command', $frontendCommand

Write-Host "Setup complete."
Write-Host "Backend: http://localhost:8000"
Write-Host "Frontend: http://localhost:4173/"

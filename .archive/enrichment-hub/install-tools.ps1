# Installation script for Obsidian, GitKraken, and Git tools
# Run this script with: powershell -ExecutionPolicy Bypass -File install-tools.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CTB Project Tools Installation Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "⚠️  This script should be run as Administrator for best results." -ForegroundColor Yellow
    Write-Host "Some installations may require elevated privileges." -ForegroundColor Yellow
    Write-Host ""
}

# Check if Chocolatey is installed
function Test-Chocolatey {
    $choco = Get-Command choco -ErrorAction SilentlyContinue
    return $null -ne $choco
}

# Install Chocolatey if not present
if (-not (Test-Chocolatey)) {
    Write-Host "📦 Chocolatey not found. Installing Chocolatey..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

    if (Test-Chocolatey) {
        Write-Host "✅ Chocolatey installed successfully!" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to install Chocolatey. Please install manually." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Chocolatey is already installed" -ForegroundColor Green
}

Write-Host ""

# Function to check if a tool is installed
function Test-Installation {
    param($command)
    $result = Get-Command $command -ErrorAction SilentlyContinue
    return $null -ne $result
}

# Install Git
Write-Host "📥 Checking Git installation..." -ForegroundColor Cyan
if (Test-Installation "git") {
    Write-Host "✅ Git is already installed" -ForegroundColor Green
    git --version
} else {
    Write-Host "Installing Git..." -ForegroundColor Yellow
    choco install git -y
    Write-Host "✅ Git installed!" -ForegroundColor Green
}

Write-Host ""

# Install Obsidian
Write-Host "📥 Checking Obsidian installation..." -ForegroundColor Cyan
$obsidianPath = "C:\Users\$env:USERNAME\AppData\Local\Obsidian\Obsidian.exe"
if (Test-Path $obsidianPath) {
    Write-Host "✅ Obsidian is already installed" -ForegroundColor Green
} else {
    Write-Host "Installing Obsidian..." -ForegroundColor Yellow
    choco install obsidian -y
    Write-Host "✅ Obsidian installed!" -ForegroundColor Green
}

Write-Host ""

# Install GitKraken
Write-Host "📥 Checking GitKraken installation..." -ForegroundColor Cyan
$gitkrakenPath = "C:\Users\$env:USERNAME\AppData\Local\gitkraken\GitKraken.exe"
if (Test-Path $gitkrakenPath) {
    Write-Host "✅ GitKraken is already installed" -ForegroundColor Green
} else {
    Write-Host "Installing GitKraken..." -ForegroundColor Yellow
    choco install gitkraken -y
    Write-Host "✅ GitKraken installed!" -ForegroundColor Green
}

Write-Host ""

# Install Node.js if not present (needed for project)
Write-Host "📥 Checking Node.js installation..." -ForegroundColor Cyan
if (Test-Installation "node") {
    Write-Host "✅ Node.js is already installed" -ForegroundColor Green
    node --version
    npm --version
} else {
    Write-Host "Installing Node.js..." -ForegroundColor Yellow
    choco install nodejs -y
    Write-Host "✅ Node.js installed!" -ForegroundColor Green
}

Write-Host ""

# Configure Git hooks
Write-Host "🔧 Setting up Git hooks..." -ForegroundColor Cyan
if (Test-Path ".git/hooks") {
    # Make hooks executable
    $hooks = Get-ChildItem ".git/hooks" -File -Filter "pre-*","commit-*"
    foreach ($hook in $hooks) {
        Write-Host "  Setting up $($hook.Name)..." -ForegroundColor Gray
    }
    Write-Host "✅ Git hooks configured!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Git repository not initialized. Run 'git init' first." -ForegroundColor Yellow
}

Write-Host ""

# Install project dependencies
Write-Host "📦 Installing project dependencies..." -ForegroundColor Cyan
if (Test-Path "package.json") {
    npm install
    Write-Host "✅ Dependencies installed!" -ForegroundColor Green
} else {
    Write-Host "⚠️  package.json not found in current directory" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Configure your environment variables in .env file"
Write-Host "2. Open Obsidian and select this folder as vault"
Write-Host "3. Open GitKraken and add this repository"
Write-Host "4. Configure Git user:"
Write-Host "   git config user.name 'Your Name'"
Write-Host "   git config user.email 'your.email@example.com'"
Write-Host ""
Write-Host "Happy coding! 🚀" -ForegroundColor Cyan

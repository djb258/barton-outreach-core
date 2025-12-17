@echo off
REM Installation script for CTB project tools
REM Run this as Administrator for best results

echo ========================================
echo CTB Project Tools Installation Script
echo ========================================
echo.

REM Check for Administrator rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: Not running as Administrator
    echo Some installations may require elevated privileges.
    echo.
    pause
)

REM Check if Chocolatey is installed
where choco >nul 2>&1
if %errorLevel% neq 0 (
    echo Installing Chocolatey package manager...
    @"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "[System.Net.ServicePointManager]::SecurityProtocol = 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
    echo Chocolatey installed!
) else (
    echo Chocolatey is already installed
)

echo.

REM Install Git
echo Checking Git installation...
where git >nul 2>&1
if %errorLevel% neq 0 (
    echo Installing Git...
    choco install git -y
    echo Git installed!
) else (
    echo Git is already installed
    git --version
)

echo.

REM Install Obsidian
echo Checking Obsidian installation...
if exist "%LOCALAPPDATA%\Obsidian\Obsidian.exe" (
    echo Obsidian is already installed
) else (
    echo Installing Obsidian...
    choco install obsidian -y
    echo Obsidian installed!
)

echo.

REM Install GitKraken
echo Checking GitKraken installation...
if exist "%LOCALAPPDATA%\gitkraken\GitKraken.exe" (
    echo GitKraken is already installed
) else (
    echo Installing GitKraken...
    choco install gitkraken -y
    echo GitKraken installed!
)

echo.

REM Install Node.js
echo Checking Node.js installation...
where node >nul 2>&1
if %errorLevel% neq 0 (
    echo Installing Node.js...
    choco install nodejs -y
    echo Node.js installed!
) else (
    echo Node.js is already installed
    node --version
)

echo.

REM Install project dependencies
echo Installing project dependencies...
if exist "package.json" (
    call npm install
    echo Dependencies installed!
) else (
    echo WARNING: package.json not found
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Configure your environment variables in .env file
echo 2. Open Obsidian and select this folder as vault
echo 3. Open GitKraken and add this repository
echo 4. Configure Git user:
echo    git config user.name "Your Name"
echo    git config user.email "your.email@example.com"
echo.
echo Happy coding!
echo.
pause

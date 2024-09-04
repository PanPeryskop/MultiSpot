@echo off
cd %~dp0

git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Git is not installed. Please install Git to continue.
    exit /b 1
)

set REMOTE_URL=https://github.com/PanPeryskop/MultiSpot

git remote get-url origin >nul 2>&1
if %errorlevel% neq 0 (
    git remote add origin %REMOTE_URL%
) else (
    git remote set-url origin %REMOTE_URL%
)

echo Checking if you have the latest version...
git fetch

setlocal enabledelayedexpansion
for /f "tokens=*" %%i in ('git rev-list HEAD...origin/main --count') do set NEW_COMMITS=%%i
if !NEW_COMMITS! neq 0 (
    echo A new version is available. Updating...
    git pull
) else (
    echo The application is up to date.
)

pythonw main.pyw
exit

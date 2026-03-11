@echo off
setlocal enabledelayedexpansion

echo =========================================
echo  Seedling Installer
echo =========================================

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Checking for pipx...
where pipx >nul 2>&1
if %errorlevel% neq 0 (
    echo      pipx not found. Attempting to install pipx...
    python -m pip install --user pipx >nul 2>&1
    python -m pipx ensurepath >nul 2>&1
    echo      Please RESTART this script or your terminal to continue.
    pause
    exit /b 0
)

echo [2/3] Installing TreeWeaver commands ('scan' ^& 'build')...
pipx install . --force
if %errorlevel% neq 0 (
    echo [ERROR] Installation failed. Try running: pipx install . --force
    pause
    exit /b 1
)

echo [3/3] Finalizing...
pipx ensurepath >nul 2>&1

echo =========================================
echo   Installation successful!
echo    - Type 'scan' to explore.
echo    - Type 'build' to construct.
echo =========================================
echo   Tip: If commands aren't found, restart your terminal.
pause
exit /b 0
@echo off
setlocal enabledelayedexpansion

echo.
echo  ############################################
echo  #                                          #
echo  #       ZEROONE BOT by HOLOCRON            #
echo  #             SETUP WIZARD                #
echo  ############################################
echo.

:: 1. Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.11+ and add it to PATH.
    pause
    exit /b 1
)

:: 2. Create Virtual Environment
echo [1/4] Creating virtual environment...
python -m venv .venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

:: 3. Install Requirements
echo [2/4] Installing dependencies (this may take a minute)...
call .venv\Scripts\activate
pip install --upgrade pip >nul
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b 1
)

:: 4. Setup Environment File
echo [3/4] Preparing .env file...
if not exist .env (
    copy .env.example .env >nul
    echo [OK] Created .env from template.
) else (
    echo [SKIP] .env already exists.
)

:: 5. Final Checks
echo [4/4] Finalizing setup...
if not exist id.json (
    echo.
    echo [IMPORTANT] Please place your 'id.json' keypair in this folder.
)

echo.
echo ############################################
echo #          SETUP COMPLETE!                 #
echo ############################################
echo.
echo To start the bot:
echo 1. Edit .env with your settings
echo 2. Run: launcher.bat (to be created) OR python launcher.py
echo.
pause

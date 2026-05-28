@echo off
cd /d "%~dp0"

echo ====================================
echo  RAG ChatBot - Setup
echo ====================================

:: [1] Python ---------------------------------------------------------
set PYTHON=
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if %errorlevel% equ 0 set PYTHON=py -3

if "%PYTHON%"=="" (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
    if %errorlevel% equ 0 set PYTHON=python
)

if "%PYTHON%"=="" (
    echo [ERROR] Python not found. Install Python 3.10+ from https://python.org
    pause
    exit /b 1
)
echo [1/4] Python OK  (%PYTHON%)

:: [2] venv -----------------------------------------------------------
if not exist "venv\Scripts\activate.bat" (
    echo [2/4] Creating virtual environment...
    %PYTHON% -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create venv.
        pause
        exit /b 1
    )
) else (
    echo [2/4] Using existing virtual environment.
)

:: [3] Packages -------------------------------------------------------
echo [3/4] Installing packages...
venv\Scripts\python.exe -m pip install --upgrade pip -q
venv\Scripts\python.exe -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Package installation failed.
    pause
    exit /b 1
)
echo [3/4] Packages OK

:: [4] Ollama ---------------------------------------------------------
echo [4/4] Checking Ollama...

set OLLAMA_DIR=%LOCALAPPDATA%\Programs\Ollama
set OLLAMA_EXE=%OLLAMA_DIR%\ollama.exe

:: Always add Ollama dir to PATH so "ollama" command works regardless
set PATH=%OLLAMA_DIR%;%PATH%

where ollama >nul 2>&1
if %errorlevel% equ 0 goto :ollama_found

:: Ollama not found - download and install
echo Ollama not found. Downloading...
set SETUP_EXE=%TEMP%\OllamaSetup.exe

where curl >nul 2>&1
if %errorlevel% equ 0 (
    curl -L --progress-bar -o "%SETUP_EXE%" "https://ollama.com/download/OllamaSetup.exe"
) else (
    echo Downloading via PowerShell...
    powershell -Command "Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile '%SETUP_EXE%'"
)

if not exist "%SETUP_EXE%" (
    echo [ERROR] Download failed. Check your internet connection.
    pause
    exit /b 1
)

echo Installing Ollama... (follow the installer window)
"%SETUP_EXE%"
del /f /q "%SETUP_EXE%" >nul 2>&1

where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Ollama not found after install. Try manually: https://ollama.com/download
    pause
    exit /b 1
)
echo Ollama installed OK.

:ollama_found
echo Ollama OK

:: Start Ollama server if not already running
netstat -an | findstr "127.0.0.1:11434" | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo Ollama server already running.
) else (
    echo Starting Ollama server...
    start "" /B ollama serve
    echo Waiting for server...
    timeout /t 5 /nobreak >nul
)

:: Pull models
echo.
echo Pulling llama3.2 - about 2GB ...
ollama pull llama3.2
if %errorlevel% neq 0 (
    echo Retrying llama3.2 ...
    ollama pull llama3.2
    if %errorlevel% neq 0 (
        echo [ERROR] Failed. Run manually: ollama pull llama3.2
        pause
        exit /b 1
    )
)

echo.
echo Pulling nomic-embed-text - about 270MB ...
ollama pull nomic-embed-text
if %errorlevel% neq 0 (
    echo Retrying nomic-embed-text ...
    ollama pull nomic-embed-text
    if %errorlevel% neq 0 (
        echo [ERROR] Failed. Run manually: ollama pull nomic-embed-text
        pause
        exit /b 1
    )
)

echo.
echo ====================================
echo  Setup complete!  Run:  run.bat
echo ====================================
echo.
pause

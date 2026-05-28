@echo off
cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found.
    echo Run setup.bat first, then run this file again.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
venv\Scripts\python.exe -m streamlit run app.py

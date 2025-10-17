@echo off
REM run_cargalugar.bat
REM Changes to the script directory, activates the virtual environment if present, and runs CargaLugar.py

:: Change to the directory containing this batch file (works when double-clicked)
cd /d "C:\Users\lmarinaro\Documents\CargaLugar"

:: If a venv python exists, activate the venv (activate.bat) and use the venv python
if exist ".venv\Scripts\python.exe" (
    echo Activating virtual environment...
    call ".venv\Scripts\activate.bat"
    echo Running CargaLugar.py with virtual environment python
    ".venv\Scripts\python.exe" "CargaLugar.py" %*
    exit /b %ERRORLEVEL%
) else (
    echo Virtual environment not found at .venv\Scripts\python.exe
    echo Falling back to system Python
    python "CargaLugar.py" %*
    exit /b %ERRORLEVEL%
)

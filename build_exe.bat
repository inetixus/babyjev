@echo off
REM BabyJev: build a single-file exe.
REM Run this once on your Windows machine. Output lands in dist\BabyJev.exe
REM Keep config.json next to the exe (that is where it reads settings from).

setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [x] Python not found. Install it from https://www.python.org/downloads/
    echo     and tick "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
python -m pip install -r requirements.txt pyinstaller --upgrade -q || goto :fail

echo [2/3] Building BabyJev.exe (30-60 seconds)...
python -m PyInstaller --onefile --name BabyJev --clean --noconfirm triggerbot.py || goto :fail

echo [3/3] Done.
echo.
echo    Your program: dist\BabyJev.exe
echo    Copy config.json next to it, then run it.
echo    First run may take a few seconds (self-extracting), that is normal.
echo.
echo    Try:  dist\BabyJev.exe --self-test
echo.
pause
exit /b 0

:fail
echo.
echo [x] Build failed. Read the messages above, fix, rerun.
pause
exit /b 1

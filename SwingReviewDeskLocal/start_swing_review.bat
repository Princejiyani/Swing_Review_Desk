@echo off
setlocal
cd /d "%~dp0"
title Swing Review Desk Launcher

where py >nul 2>nul
if not errorlevel 1 (
  set "PYRUN=py -3"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python 3 was not found on this computer.
    echo Install Python 3.10 or newer from https://www.python.org/downloads/windows/
    echo During installation, enable the option to add Python to PATH.
    pause
    exit /b 1
  )
  set "PYRUN=python"
)

echo Checking Python and installing the required data package...
%PYRUN% --version
if errorlevel 1 goto failed
%PYRUN% -m pip install -r requirements.txt
if errorlevel 1 goto failed

rem Find Chrome directly so Windows' default browser (Edge) is not used.
set "CHROME="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not defined CHROME if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not defined CHROME if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "CHROME=%LocalAppData%\Google\Chrome\Application\chrome.exe"
if not defined CHROME (
  echo.
  echo Google Chrome was not found in the usual installation folders.
  echo Install Chrome, then run this launcher again.
  pause
  exit /b 1
)

echo Starting Swing Review Desk in this window...
set "SWING_REVIEW_CHROME=%CHROME%"
echo The app will open in Google Chrome. Keep this window open while using it.
echo Press Ctrl+C here to stop the server.
echo.
%PYRUN% server.py
exit /b %errorlevel%

:failed
echo.
echo Setup failed. Check your internet connection and Python installation, then run this file again.
pause
exit /b 1

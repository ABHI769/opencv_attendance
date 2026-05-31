@echo off
title Attendance System Launcher
color 0A
echo.
echo ========================================
echo    Face Recognition Attendance System
echo ========================================
echo.
echo Starting servers...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Start the application
python start.py

pause

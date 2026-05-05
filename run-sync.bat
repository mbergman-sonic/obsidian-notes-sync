@echo off
REM Obsidian Daily Sync - Interactive Runner
REM This script provides an easy way to run the sync manually with options

setlocal enabledelayedexpansion

title Obsidian Daily Sync

echo.
echo ===============================================================
echo          OBSIDIAN DAILY SYNC - Manual Runner
echo ===============================================================
echo.
echo Options:
echo   1. Run sync now
echo   2. Test connectivity
echo   3. Run sync with verbose output
echo   4. Exit
echo.

set /p choice="Choose an option (1-4): "

if "%choice%"=="1" (
    echo.
    echo Running sync...
    cd /d "C:\Users\michael.bergman\Projects\obsidian-daily-sync"
    python sync_daily_notes.py
    echo.
    echo Sync complete. Press any key to exit.
    pause > nul
    exit /b 0
)

if "%choice%"=="2" (
    echo.
    echo Testing connectivity...
    cd /d "C:\Users\michael.bergman\Projects\obsidian-daily-sync"
    python sync_daily_notes.py --test
    echo.
    echo Test complete. Press any key to exit.
    pause > nul
    exit /b 0
)

if "%choice%"=="3" (
    echo.
    echo Running sync with verbose output...
    cd /d "C:\Users\michael.bergman\Projects\obsidian-daily-sync"
    python sync_daily_notes.py --verbose
    echo.
    echo Sync complete. Press any key to exit.
    pause > nul
    exit /b 0
)

if "%choice%"=="4" (
    exit /b 0
)

echo.
echo Invalid choice. Press any key to exit.
pause > nul
exit /b 1


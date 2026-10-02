@echo off
setlocal enabledelayedexpansion

:: ============================================================
::  BidSentry AI Launcher
::  Double-click this file to start the full stack
:: ============================================================

echo.
echo  =====================================================
echo   ____  _     _ _____            _
echo  | __ )(_) __| / ____|          | |
echo  |  _ \| |/ _` \___ \ ___ _ __ | |_ _ __ _   _
echo  | |_) | | (_| |___) / _ \ '_ \| __| '__| | | |
echo  |____/|_|\__,_|____/\___/_| |_|\__|_|  \__, |
echo                                           __/ |
echo   Bid Intelligence ^& Compliance Co-Pilot|___/
echo  =====================================================
echo.

:: --- Step 1: Verify system services -----------------------
echo [1/3] Running system verification...
echo.
python verify_system.py
echo.

:: --- Step 2: Open browser (non-blocking) ------------------
echo [2/3] Opening browser at http://localhost:8000 ...
start http://localhost:8000
echo.

:: --- Step 3: Start bridge server (blocking) ---------------
echo [3/3] Starting BidSentry Bridge Server...
echo       Press Ctrl+C to stop.
echo.
python server.py

endlocal

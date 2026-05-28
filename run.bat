@echo off
REM Test Docs Platform - Launcher Script (Windows)
REM 用法: run.bat --help
REM       run.bat --interactive "https://login.dev.ehr.gov.hk/pfw-logon/logon" --session-name "My Test"

set SCRIPT_DIR=%~dp0
set VENV_PYTHON=%SCRIPT_DIR%.venv\Scripts\python.exe

REM 初始化數據庫（忽略錯誤）
"%VENV_PYTHON%" "%SCRIPT_DIR%main.py" --init-db 2>nul

REM 執行主程序
"%VENV_PYTHON%" "%SCRIPT_DIR%main.py" %*
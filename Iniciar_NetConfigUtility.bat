@echo off
title NetConfigUtility v1.0
cd /d "%~dp0"
python NetConfigSwitcher.py
if %errorlevel% neq 0 (
    pause
)


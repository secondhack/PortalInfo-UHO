@echo off
cd /d "%~dp0.."
".venv\Scripts\python.exe" scripts\check_environment.py
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -u scripts\serve_backend.py

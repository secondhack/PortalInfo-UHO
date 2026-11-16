@echo off
cd /d "%~dp0.."
"C:\Program Files\PostgreSQL\16\bin\pg_ctl.exe" -D "%CD%\.local\postgres" stop -m fast

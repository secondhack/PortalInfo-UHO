@echo off
cd /d "%~dp0.."
"C:\Program Files\PostgreSQL\16\bin\pg_ctl.exe" -D "%CD%\.local\postgres" -l "%CD%\.local\postgres.log" -o "-h 127.0.0.1 -p 55432" start

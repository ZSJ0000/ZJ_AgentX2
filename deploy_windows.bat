@echo off
cd /d "%~dp0"
python deploy.py %*
if errorlevel 1 exit /b %errorlevel%

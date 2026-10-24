@echo off
setlocal
set "REPO=https://github.com/ZSJ0000/ZJ_AgentX2.git"
if "%ZJ_AGENTX2_DIR%"=="" (set "DIR=%USERPROFILE%\ZJ_AgentX2") else (set "DIR=%ZJ_AGENTX2_DIR%")
set "ARGS="
:args
if "%~1"=="" goto run
if /i "%~1"=="--dir" set "DIR=%~2"&shift&shift&goto args
if /i "%~1"=="--no-venv" set "ARGS=%ARGS% --no-venv"&shift&goto args
if /i "%~1"=="--skip-tests" set "ARGS=%ARGS% --skip-tests"&shift&goto args
if /i "%~1"=="--start" set "ARGS=%ARGS% --start"&shift&goto args
echo Unknown option: %~1&exit /b 2
:run
if exist "%DIR%\.git" (git -C "%DIR%" pull --ff-only) else (git clone "%REPO%" "%DIR%")
if errorlevel 1 exit /b %errorlevel%
cd /d "%DIR%"
python deploy.py %ARGS%
if errorlevel 1 exit /b %errorlevel%
echo [install] complete: %DIR%
echo [install] edit: %DIR%\config.json
echo [install] start: start_windows.bat
endlocal

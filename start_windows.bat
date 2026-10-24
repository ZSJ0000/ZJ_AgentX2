@echo off
cd /d "%~dp0"
set "ZJ_MODE=%~1"
if /I "%ZJ_MODE%"=="cli" (if exist .venv\Scripts\python.exe (.venv\Scripts\python.exe -m zj_agentx2 --config config.json --mode cli --task "%~2") else (python -m zj_agentx2 --config config.json --mode cli --task "%~2") & exit /b)
if exist .venv\Scripts\python.exe (.venv\Scripts\python.exe -m zj_agentx2 --config config.json --mode auto) else (python -m zj_agentx2 --config config.json --mode auto)

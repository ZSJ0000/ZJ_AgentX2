@echo off
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (.venv\Scripts\python.exe -m zj_agentx2 --config config.json --task "%~1") else (python -m zj_agentx2 --config config.json --task "%~1")

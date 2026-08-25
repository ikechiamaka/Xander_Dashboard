@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Create the environment first: python -m venv .venv
  exit /b 1
)
".venv\Scripts\python.exe" run_pipeline.py

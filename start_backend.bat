@echo off
echo Starting MultiSpot Backend...
cd /d "%~dp0backend"
uv run uvicorn main:app --reload --port 8000

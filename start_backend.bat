@echo off
echo Starting MultiSpot Backend...
call d:\projekty\MultiSpot\.venv\Scripts\activate.bat
cd backend
python -m uvicorn main:app --reload --port 8000

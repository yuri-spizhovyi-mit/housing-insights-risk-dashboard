@echo off
set PYTHONPATH=services/fastapi
cd services\fastapi
uvicorn main:app --reload --port 8000
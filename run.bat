@echo off
cd /d %~dp0
python main.py >> logs\app.log 2>&1
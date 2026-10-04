@echo off
rem Starts the course app and opens it in your browser.
rem Keep the window that opens; close it when you're done studying.
cd /d "%~dp0"
python app\server.py
if errorlevel 1 pause

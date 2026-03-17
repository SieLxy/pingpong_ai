@echo off
setlocal
cd /d %~dp0
for /f %%i in ('powershell -NoLogo -Command "(Get-Date).ToString('yyyyMMdd-HHmmss')"') do set TS=%%i
set LOG_FILE=logs\run-%TS%.log
set LOG_FILE_PATH=%CD%\%LOG_FILE%
if not exist logs mkdir logs
set PY311=C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe
if exist "%PY311%" (
  set PY_EXE=%PY311%
) else (
  set PY_EXE=python
)
if not exist .venv (
  echo [1/4] Creating venv with %PY_EXE% ...
  "%PY_EXE%" -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
set PORT=8000
echo [4/4] Starting server on port %PORT% ...
uvicorn app.main:app --host 0.0.0.0 --port %PORT% >> "%LOG_FILE%" 2>&1
endlocal

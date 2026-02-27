@echo off
setlocal

if not exist .venv (
  python -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
playwright install chromium
python semasa_bot.py --excel dados.xlsx

endlocal

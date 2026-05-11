@echo off
echo ============================================================
echo  Centrica Tail-Spend Agent Demo — Setup and Launch
echo ============================================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.11+ from python.org
    pause
    exit /b 1
)

echo [1/4] Creating virtual environment...
python -m venv .venv
call .venv\Scripts\activate.bat

echo [2/4] Installing dependencies...
pip install --upgrade pip -q
pip install openai>=1.50 streamlit>=1.36 plotly>=5.22 python-dotenv>=1.0 pydantic>=2.8 tenacity>=9.0 python-docx>=1.1 openpyxl>=3.1

echo [3/4] Checking .env file...
if not exist .env (
    copy .env.example .env
    echo.
    echo IMPORTANT: .env file created. Please open it and paste your OpenAI API key.
    echo The app will still run in demo mode without a key.
    echo.
)

echo [4/4] Launching Streamlit app...
echo.
echo  Open: http://localhost:8501
echo  Press Ctrl+C to stop.
echo.
streamlit run app.py --server.port 8501 --server.headless false

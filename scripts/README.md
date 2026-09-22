# RakeGlossary Scripts

Quick-launch scripts for Windows.

## First time setup

Double-click **`setup.bat`**.

It will:
1. Create a Python venv (if missing)
2. Install backend dependencies (`pip install -e ".[dev]"`)
3. Download the spaCy English model (`en_core_web_sm`)
4. Download NLTK data (stopwords, punkt, punkt_tab)
5. Install frontend dependencies (`npm install`)

## Daily development

Double-click **`dev.bat`**.

It opens two terminal windows:
- **Backend** on `http://127.0.0.1:8765`
- **Frontend** on `http://localhost:5173`

Close both windows to stop the servers.

## Running servers individually

- `dev-backend.bat` — only the FastAPI backend
- `dev-frontend.bat` — only the Vite frontend

## Troubleshooting

### "No venv found"
Run `setup.bat` first.

### Backend fails to import `fastapi`
The venv is not the one that has dependencies installed.
Check that `..\venv312\Scripts\python.exe` exists, or edit the
`VENV_DIR` search list at the top of `dev-backend.bat`.

### Port 8765 already in use
Another backend is running. Kill it with:
netstat -ano | findstr :8765
taskkill /PID <PID> /F


### Port 5173 already in use
Vite will pick the next free port and print it in the terminal.

### NLTK download fails behind a proxy
The scripts already set `NLTK_ALLOW_PROXIED_URLOPEN=1`.
If the problem persists, download the data manually:
python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('punkt_tab')"


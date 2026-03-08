# Backend (FastAPI + SQLite)

## Setup
1. Create a virtual environment and install dependencies.
   ```bash
   cd /Users/petar/repos/HumanResources/backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Run the API.
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

## Endpoints
- `GET /health`
- `POST /users` (email + password)

SQLite database file is created at `backend/app.db` on first startup.

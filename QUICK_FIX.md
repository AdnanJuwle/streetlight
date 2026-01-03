# Quick Fix: Starting the Backend

## ✅ CORRECT WAY (Run from backend directory):

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## ❌ DON'T run from project root with `backend.main:app`

The imports are set up to work when running from the `backend/` directory.

## Alternative: Use the batch file

```bash
start_backend.bat
```

This automatically changes to the backend directory and starts the server.

## Verify it's working

Once started, you should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

Then test:
- http://localhost:8000/health
- http://localhost:8000/api/v1/devices


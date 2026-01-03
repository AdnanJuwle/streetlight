# ⚠️ IMPORTANT: Restart Backend After Database Path Fix

## The Problem
The backend was connecting to a different (empty) database file when running from the `backend/` directory.

## The Fix
I've updated the database path to use an absolute path to the project root, so it always uses the same database file.

## What You Need to Do

1. **Stop the current backend** (Press Ctrl+C in the terminal running the backend)

2. **Restart the backend**:
   ```bash
   cd backend
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Verify it's working**:
   ```bash
   curl http://localhost:8000/api/v1/devices
   ```
   Should now return 4 devices instead of `[]`

4. **Refresh your frontend** at http://localhost:3000

## Expected Result

After restarting, you should see:
- ✅ 4 devices in the device list
- ✅ 5 active alerts in the alerts panel
- ✅ Device markers on the map
- ✅ ML predictions when you click on a device


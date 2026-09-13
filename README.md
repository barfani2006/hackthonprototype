# Advanced Coal Mine Digital Twin

This package preserves the current reference-style simulation UI and adds online deployment configuration.

## Local run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m backend.server
```

Open `http://127.0.0.1:8000`.

## Online deployment with Render

1. Upload this folder to GitHub.
2. Create a Render **Web Service** from the repository.
3. Use:

   - Build command: `pip install -r requirements.txt`
   - Start command: `python -m backend.server`

The server listens on `0.0.0.0` and automatically uses Render's `PORT` environment variable.

## Docker deployment

```bash
docker build -t coal-mine-digital-twin .
docker run -p 8000:8000 coal-mine-digital-twin
```

## Important

This remains a simulation-only application. It is not connected to real mine equipment or control systems.

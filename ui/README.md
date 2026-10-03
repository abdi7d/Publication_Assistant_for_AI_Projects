# UI

This folder contains a static Tailwind CSS-based UI for the Publication Assistant.

- `index.html`: Dark-themed dashboard mockup matching the provided design screenshot. It's a static frontend that can be served directly or integrated into the app.

How to run locally:

1. Open `ui/index.html` in a browser. No build step required because it uses the Tailwind CDN.

2. Or serve it via the backend FastAPI mode (recommended to enable live agent integration and API calls):

```bash
pip install -r requirements.txt
python app.py --serve-ui --host 0.0.0.0 --port 8000
```

Then open `http://localhost:8001` to use the static dashboard connected to the Python backend API.

Optional next steps:

- Integrate the UI with the Python backend (`app.py` / `main.py`) by serving the `ui/` folder via a static file route (FastAPI/Starlette).
- Replace placeholders with dynamic content and wire up repository validation and generation endpoints.

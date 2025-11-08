
# Deploying to Render (frontend + backend separately)

This document shows a minimal set of steps to deploy the Educator AI Assistant
project on Render with two separate services: a FastAPI backend and a React
frontend (Create React App) served as a Static Site.

Files added/used:
- `render.yaml` (top-level) — declares two Render services: `educatorai-backend`
	and `educatorai-frontend`.

High-level checklist
- Backend: Python FastAPI app (entry: `app.main:app`) — run with uvicorn.
- Frontend: React (CRA) in `educator-ai-assistant/frontend` — build with `npm run build` and publish `build/`.
- Frontend must know the backend URL; set `REACT_APP_API_URL` in Render's Static Site env vars.

1) Prepare the repo
- Commit any changes (we added a small change so the frontend reads `REACT_APP_API_URL`).

2) Frontend changes (already applied)
- The frontend's API client now prefers `process.env.REACT_APP_API_URL`, then
	`window.API_BASE_URL`, then falls back to `http://localhost:8003` for local dev.

3) Using the `render.yaml`
- Connect your GitHub repo to Render.
- In Render, choose to create services from `render.yaml` (or manually create two services):
	- A Web Service named `educatorai-backend` (Python). Build command: `pip install -r requirements.txt`. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
	- A Static Site named `educatorai-frontend`. Build command (in `render.yaml`): `cd educator-ai-assistant/frontend; npm install; npm run build`. Publish directory: `educator-ai-assistant/frontend/build`.

4) Environment variables
- Backend: set any secrets needed (e.g., `DATABASE_URL`, `JWT_SECRET`, API keys). Configure them in the Render dashboard for the backend service.
- Frontend: set `REACT_APP_API_URL` to your backend URL, e.g. `https://educatorai-backend.onrender.com`.

5) Optional: CORS and health checks
- Backend already uses CORS middleware (check `app/main.py`), but ensure the frontend origin is allowed if you're using strict CORS.
- Add a health check path in Render for the backend (e.g., `/health`) if you want uptime checks.

6) Quick local verification
- Backend: run locally with `uvicorn app.main:app --reload --port 8003` from `educator-ai-assistant` root.
- Frontend: from `educator-ai-assistant/frontend`: `npm install` then `npm run build` and `serve -s build` (or `npm start` for dev with proxy). When building for Render, the `REACT_APP_API_URL` is baked into the build.

Notes and gotchas
- CRA environment variables: `process.env.REACT_APP_*` are injected at build time. When you set `REACT_APP_API_URL` in Render's Static Site env, it will be used during the `npm run build` step.
- If you prefer runtime configuration (no rebuild per backend URL change), set `window.API_BASE_URL` at runtime via a tiny script in `index.html` that reads from a hosted runtime config. We kept support for `window.API_BASE_URL` as a fallback.

If you'd like, I can:
- Add a tiny `index.html` snippet to optionally set `window.API_BASE_URL` from a JSON file hosted alongside the static assets (runtime config), or
- Create a Render `service` variant that runs the frontend as a Node web service.


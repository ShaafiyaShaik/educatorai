Deployment note:
	duplicate schedule rows locally. DB backups were created but not committed.
	These scripts are in `scripts/` and can be used to recover or clean local
	SQLite databases before deploying. No database files were added to the repo.

Render deployment troubleshooting (login failing / ERR_CONNECTION_REFUSED)
If the deployed frontend shows errors like "Failed to load resource: net::ERR_CONNECTION_REFUSED http://localhost:8003/..." then the frontend was built with a development default API URL (`http://localhost:8003`). In production (Render) the frontend must call the deployed backend URL instead of `localhost`.

Quick fix (recommended):
 
Deployment notes:
- Set the backend `DATABASE_URL` environment variable in the Render dashboard to point
	at the database you want the deployed backend to use. The app will prefer:
	1) `DATABASE_URL` env var
	2) `PRODUCTION_DATABASE_URL` env var
	3) A repository file named `DEPLOY_DATABASE_URL` (if present)
	4) Fallback to `sqlite:///./educator_db.sqlite` (local development)

If you want the Render service to use the recovered demo DB quickly for a demo,
you may commit `educator_db.sqlite` to the repo and set `DATABASE_URL=sqlite:///./educator_db.sqlite`.
This is convenient for demonstrations but not recommended for production.


Why this helps:
- The frontend uses the `REACT_APP_API_BASE_URL` environment variable (in `frontend/src/services/api.js`) to build API requests. If this variable is not set at build time, the compiled frontend falls back to `http://localhost:8003` which will fail in Render.

Other notes:
- The `AbortError: The play() request was interrupted by a call to pause()` message is a browser/media warning (often from an audio/video element) and is unrelated to login connectivity.
- We intentionally did not commit any database files or backups to the repo.

If you'd like, I can:
- Add a small `scripts/README.md` with run examples for the dedupe scripts.
- Open the repo in your browser and confirm the commit is visible.
- Attempt to detect your backend URL (if you give it) and set `REACT_APP_API_BASE_URL` in a new commit, but note Render environment variables must be configured through the Render dashboard (I cannot set them from the repo).



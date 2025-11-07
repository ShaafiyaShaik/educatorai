# Deployment guide

This file describes simple ways to deploy the project frontend and backend.

Option A — Frontend on Vercel, Backend on Replit / Render (recommended)

1. Frontend (Vercel)
   - Go to https://vercel.com and import the GitHub repository.
   - Select the `frontend` directory as the project root (there's a `package.json` there).
   - Build command: `npm run build` (Vercel auto detects for Create React App).
   - Output directory: `build`.
   - (Optional) Add environment variables in Vercel for frontend if any.

2. Backend (Replit)
   - Go to https://replit.com and create a new Repl by importing the GitHub repository.
   - Replit will use the `.replit` file to run the project. It installs `requirements.txt`, `npm install` in the frontend, and starts `uvicorn`.
   - Add environment variables (database URLs, API keys) via the Replit Secrets UI.

3. Connect frontend to backend
   - After the backend is running, note its public URL (e.g., https://your-repl.username.repl.co).
   - The frontend production build reads the backend URL from the environment variable `REACT_APP_API_BASE_URL` (this is required by Create React App). If you don't set it, the frontend will use the same origin as the site.
   - In Vercel: go to Project Settings → Environment Variables and add `REACT_APP_API_BASE_URL` with the backend URL (for example `https://my-backend.onrender.com`). Then redeploy the frontend.
   - Alternatively, you can change the value in `frontend/src/services/api.js` locally and rebuild, but using the environment variable is recommended.

Option B — Full deploy on Render (or Heroku)

1. Create a Render web service (or Heroku app) and point it to the repository.
2. Use the `Procfile` to start the app. Set the build command to install Python dependencies:

   pip install -r requirements.txt

3. Set environment variables (PORT, DB credentials, API keys) in the service dashboard.

Notes and follow-ups
- Consider cleaning the repo history to remove `frontend/node_modules` and local DB files that were committed. I can help with a safe plan to remove them and rewrite history.
- Make sure to remove any secrets accidentally committed and rotate them.
- If you prefer, I can create a small script to serve the frontend from FastAPI so you can deploy only the backend and serve static files from the same host.

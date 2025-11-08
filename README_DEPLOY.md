This file contains steps to deploy the repository to Vercel.

Two recommended approaches are provided: (A) use the repository root `vercel.json` (already included) which instructs Vercel how to build the frontend subfolder, or (B) import the repo in Vercel and set the project Root Directory to the frontend folder.

Quick steps (recommended - Root Directory method):

1. Go to https://vercel.com and sign in / sign up with GitHub.
2. From the Vercel dashboard click "New Project" → "Import Git Repository" and select `ShaafiyaShaik/educatorai`.
3. When prompted for settings set:
	 - Root Directory: `educator-ai-assistant/frontend`
	 - Framework Preset: Create React App (or leave auto-detect)
	 - Build Command: `npm run build`
	 - Output Directory: `build`
4. Add any required environment variables (see below) and Deploy.

Alternative: Use the included `vercel.json` at the repo root

- The repository already contains `vercel.json` which tells Vercel to build from `educator-ai-assistant/frontend/package.json` using `@vercel/static-build` and serve the `build` output. If you import the repo normally, Vercel will read this file and run the proper build.

Local test commands (PowerShell):

		cd educator-ai-assistant/frontend
		npm install
		npm run build

Environment / runtime notes

- The frontend `package.json` currently uses a `proxy` set to `http://localhost:8003`. In production you should replace local API usage with an environment variable for the API base URL. CRA reads env vars prefixed with `REACT_APP_`.
	- Example: set `REACT_APP_API_BASE_URL=https://api.example.com` in Vercel Project Settings → Environment Variables.

- Make sure any server (backend) endpoints are deployed and reachable from the deployed frontend. If the backend requires authentication keys, add them in Vercel's Environment Variables as well.

Troubleshooting

- If the build fails due to ESLint, the frontend package.json already disables eslint during build with `DISABLE_ESLINT_PLUGIN=true` in the `build` script.
- If Vercel picks the wrong root or build command, adjust those values in the Vercel project settings.

What I changed

- Added `vercel.json` at the repo root to point Vercel at the CRA frontend in `educator-ai-assistant/frontend`.

If you want, I can:
- Create a small `.vercelignore` to avoid uploading large files (node_modules) to Vercel.
- Open a PR and push the changes to the GitHub repository (I can prepare commits here; you will need to push or authorize CI to push).

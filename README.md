# Thirukkural Classifier

This repository contains a Vite/React frontend and a FastAPI backend. Deploy the
frontend to Vercel and the backend to Render as separate services.

## Deploy the backend to Render

1. Push the latest project changes to GitHub.
2. In Render, select **New + → Web Service**, connect GitHub, and choose
   `Abpokelove/thirukkural_classfier`.
3. Set the service name to `thirukkural-classifier-api`.
4. Select **Python 3** and the branch containing the deployment changes.
5. Leave **Root Directory** empty. The backend reads the corpus from
   `data/processed/thirukkural.json` at the repository root.
6. Choose the Singapore region (or another region close to your users). Select
   the Free instance if you want to start without a monthly compute charge.
7. Set the commands:
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`
8. Select **Deploy Web Service**. Once deployment finishes, copy the service
   URL, for example `https://thirukkural-classifier-api.onrender.com`.
9. Check `https://YOUR-RENDER-URL/api/health`. The response should have
   `"status": "ok"`.

## Deploy the frontend to Vercel

1. In Vercel, select **Add New → Project** and import
   `Abpokelove/thirukkural_classfier`.
2. Set the project name to `thirukkural-classifier`.
3. Set **Root Directory** to `frontend`.
4. Use these build settings:
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. Add an Environment Variable:
   - **Name:** `VITE_API_BASE_URL`
   - **Value:** the Render service URL, such as
     `https://thirukkural-classifier-api.onrender.com` (no trailing slash)
   - **Environment:** Production
6. Deploy and copy the production Vercel URL, such as
   `https://thirukkural-classifier.vercel.app`.

## Connect the frontend and backend

1. In Render, open the backend service's **Environment** settings.
2. Add this Environment Variable:
   - **Key:** `FRONTEND_ORIGINS`
   - **Value:** the exact Vercel production origin, such as
     `https://thirukkural-classifier.vercel.app` (no trailing slash)
3. If you use a custom frontend domain, include it as another comma-separated
   origin, for example:
   `https://thirukkural-classifier.vercel.app,https://www.example.com`
4. Save the variable and let Render restart/redeploy the backend.
5. Open the Vercel site and try the verification and corpus browsing features.

The backend allows `http://localhost:5173` for local development. Production
frontend domains must be listed in `FRONTEND_ORIGINS`; Vercel preview domains
are not automatically allowed.

## Local development

Run the backend from the repository root:

```powershell
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

In another terminal, run the frontend:

```powershell
cd frontend
npm install
npm run dev
```

When `VITE_API_BASE_URL` is not set, the frontend uses Vite's `/api` proxy to
`http://localhost:8000`.

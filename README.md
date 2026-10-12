# Thirukkural Classifier

This repository contains a Vite/React frontend and a FastAPI backend. Deploy the
frontend to Vercel and the backend to Render as separate services.

## Quotation classifications

The verifier reports wording classifications such as exact, formatting-normalized,
partial, modified, blended, paraphrased, fabricated, and ambiguous. It also checks
whether a complete Kural preserves the source's two canonical lines, line order,
and punctuation. This corresponds to the traditional four-seer first line and
three-seer second line; the verifier compares with the corpus's canonical lines
rather than treating whitespace-separated words as seer. A one-line rendering,
changed line division, missing final period, or extra words causes
`NOT_KURAL_STRUCTURE`; the original text-match category remains available as
`content_status`.

For example, an exact two-line Kural 1 including its final period is reported as
`AUTHENTIC_EXACT` with `structure_status: KURAL_STRUCTURE`. The same text on one
line or without its final period is reported as `NOT_KURAL_STRUCTURE`, with the
closest source in `evidence.matched_kural` and the structural findings in
`structure_issues`. Extra words are listed in `extra_words`.

## Deploy the backend to Render

1. Push the latest project changes to GitHub.
2. In Render, select **New + → Web Service**, connect GitHub, and choose
   `Abpokelove/thirukkural_classfier`.
3. Set the service name to `thirukkural-classifier-api`.
4. Select **Python 3** and the branch containing the deployment changes. The
   repository's `.python-version` file pins Render to Python 3.12.10; do not
   override it with Python 3.14.
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

The Python version pin is needed because the current dependency lock versions
include `pydantic-core==2.23.4`, which does not provide a Python 3.14 wheel.
When Render uses Python 3.14, pip tries to compile it from source and the build
fails. Python 3.12 has a compatible prebuilt wheel. For an already-created
Render service, also set `PYTHON_VERSION` to `3.12.10` in its Environment
settings, then use **Manual Deploy → Clear build cache & deploy**.

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
   - **Value:** `https://thirukkural-classfier.vercel.app`
3. If you use a custom frontend domain, include it as another comma-separated
   origin, for example:
   `https://thirukkural-classfier.vercel.app,https://www.example.com`
4. Save the variable and let Render restart/redeploy the backend.
5. Open the Vercel site and try the verification and corpus browsing features.

The backend allows `http://localhost:5173` for local development and the
production Vercel origin above. Additional production frontend domains can be
listed in `FRONTEND_ORIGINS`; Vercel preview domains are not automatically
allowed.

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

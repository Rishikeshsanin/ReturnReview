# ReturnReview: Faculty Demo Without Railway

This is an **isolated local deployment** using the real project code and the production CV release `cv-lightweight-1`. It does not alter the expired Railway deployment, cannot recover Railway's existing database rows, and does not require a new Railway account.

## Requirements

- Windows laptop with Docker Desktop running (Linux containers)
- Working internet connection for the first Docker build and Gemini requests
- Sufficient free memory/disk for Docker, PostgreSQL, the Next.js build, and CPU PyTorch / YOLO
- Gemini API key **for live LLM generation**; without a valid key, the other features can still be demonstrated but LLM is not live

## Start (PowerShell)

```powershell
git clone https://github.com/Rishikeshsanin/ReturnReview.git
cd ReturnReview
.\start-demo.ps1
```

The first run creates `.env.demo` and stops so you can edit it. Set a **unique local alphanumeric PostgreSQL password**. For the LLM demo, add your Gemini API key and set `RETURNREVIEW_LLM_ENABLED=true`; keep the file private.

Then run again:

```powershell
.\start-demo.ps1
```

The first backend Docker build downloads the approved `cv-lightweight-1` GitHub Release checkpoints and verifies their checksums. It uses **CPU PyTorch + MobileNetV3-Small + YOLO11n-seg**, not CLIP. The local PostgreSQL database is new and is stored in a named Docker volume. The frontend is compiled with `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` so the browser calls the local API.

## Validate before presenting

Open:

- Web: http://localhost:3000
- Health: http://localhost:8000/health
- Readiness: http://localhost:8000/readiness
- Metrics: http://localhost:8000/api/metrics

Expect PostgreSQL as the backend, durable persistence true, CV version `cv-lightweight-1`, CV ready true, and LLM ready true **only when configured with a valid Gemini key**.

Rehearse the real path: create a case → upload 2–4 cardboard-box images → inspect CV overlay → generate Gemini review → show exact policy → human review decision → audit timeline. Preload the images locally; do not rely on the Wi-Fi for demo photos.

## Troubleshooting

```powershell
docker compose --env-file .env.demo -f compose.demo.yml ps
docker compose --env-file .env.demo -f compose.demo.yml logs --tail=100 api
docker compose --env-file .env.demo -f compose.demo.yml logs --tail=100 web
```

If the LLM API is rate-limited or the key isn't available, the system may use deterministic fallback rather than a live Gemini call. Explain that transparently and show the historical real Gemini evaluation in the Evaluation tab. Do not claim a live LLM call occurred when it did not.

To stop without deleting the DB:

```powershell
docker compose --env-file .env.demo -f compose.demo.yml down
```

**Never run `down -v` during your presentation preparation**, as that deletes the local Postgres volume.

**Security:** `.env.demo` is intentionally ignored by Git. Do not commit keys, database URLs, or secrets to GitHub or share them in messages.

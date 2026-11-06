# ReturnReview — Working with LLMs Presentation UX v2

**Purpose:** isolated, polished faculty-review interface. This branch changes the presentation UX, not the original core CV/Gemini inference, policy retrieval, database models, or historical evaluation results.

- Branch: `presentation/working-with-llms-ux-v2`
- Intended folder: `F:\Downloads\returnreview wllm presentation`
- Presentation UI: `http://localhost:3100`
- Presentation API: `http://localhost:8100`
- Original verified project: `F:\Projects\ReturnReview` on `main`, with UI `http://localhost:3000`
- The presentation uses its **own PostgreSQL volume**. Editing or stopping the presentation Compose stack does not change the original database.

## Safest setup on Windows

1. Open Docker Desktop (Linux containers), ensure Engine running.
2. Open PowerShell and run:

```powershell
New-Item -ItemType Directory -Force -Path "F:\Downloads\returnreview wllm presentation" | Out-Null
cd "F:\Downloads\returnreview wllm presentation"
git clone --branch presentation/working-with-llms-ux-v2 --single-branch https://github.com/Rishikeshsanin/ReturnReview.git .
```

Only clone into an **empty folder**. If the folder already has files, inspect it instead of overwriting them.

3. Reuse your **private** local config, without typing any secrets into chat:

```powershell
Copy-Item "F:\Projects\ReturnReview\.env.demo" ".\.env.demo"
```

Do not commit `.env.demo`. This copy contains your Gemini key and local Postgres password.

4. First presentation build:

```powershell
.\start-presentation.ps1 -Build
```

Open `http://localhost:3100`. This first build reuses the existing production CV model release but may have to build its own images.

5. Later starts (no rebuild):

```powershell
cd "F:\Downloads\returnreview wllm presentation"
.\start-presentation.ps1
```

6. Stop **only** presentation:

```powershell
docker compose --env-file .env.demo -f compose.presentation.yml stop
```

To return to the original verified app:

```powershell
cd "F:\Projects\ReturnReview"
docker compose --env-file .env.demo -f compose.demo.yml up -d
```

Open `http://localhost:3000`. No `git checkout` or branch switching is required in your original folder.

**Never run `docker compose down -v` on either project.** It deletes the relevant Postgres volume. Do not delete the original repo or migrate its Docker Compose names.

## Presentation UX improvements

- Bigger, clearly labeled touch targets, stronger contrast and keyboard focus rings
- Faculty-presentation branding so you can distinguish it from the original version
- Guided four-stage workflow: photos → CV → Gemini review → human decision
- Easier form with optional one-click example fill
- Clear status and readiness cards, accessible validation errors and success feedback
- Image zoom and original/mask comparison controls for faculty discussion
- Confirmation before human approve/reject/request-evidence decisions
- Responsive layout and reduced-motion support
- Updated MobileNetV3-Small + YOLO11n-seg wording (removes outdated OpenCLIP language)

### Data and facts

The trained model release is still `cv-lightweight-1`. The Gemini agent still uses exactly three read-only tools, structured output and a deterministic grounding guard. Metrics are the actual reviewed public-pilot/historical values. The UX does not claim improved CV accuracy or new LLM evaluation metrics.

## Optional: copy the original demo cases into the presentation database

**Only if you want to show your already-approved case in the new presentation UI.** The default presentation DB starts empty because it is isolated. This operation reads the original database and restores a separate snapshot into the presentation database. It does not change original records.

Run this **only after you've started both projects at least once**, and **before creating any new cases in the presentation database** (the restore replaces its contents). In PowerShell:

```powershell
# Read-only export from original DB
docker exec returnreview-demo-db-1 pg_dump -U returnreview -d returnreview -Fc -f /tmp/returnreview-source-demo.dump
docker cp returnreview-demo-db-1:/tmp/returnreview-source-demo.dump "F:\Downloads\returnreview wllm presentation\returnreview-source-demo.dump"

# Stop presentation web/API only; KEEP the presentation DB running
cd "F:\Downloads\returnreview wllm presentation"
docker compose --env-file .env.demo -f compose.presentation.yml stop web api

# Restore the original snapshot into the separate presentation DB
docker cp ".\returnreview-source-demo.dump" returnreview-wllm-presentation-db-1:/tmp/demo-seed.dump
docker compose --env-file .env.demo -f compose.presentation.yml exec -T db pg_restore -U returnreview -d returnreview --clean --if-exists --no-owner --no-privileges /tmp/demo-seed.dump

# Restart presentation web/API
docker compose --env-file .env.demo -f compose.presentation.yml up -d
```

When `pg_restore` completes, confirm approved cases appear on `http://localhost:3100`. The source container remains unchanged.

The export contains potentially sensitive case/image records and must not be committed to GitHub or shared publicly. If any restore error occurs, stop and inspect the error instead of repeatedly restoring.

## Safety checks

```powershell
docker compose --env-file .env.demo -f compose.presentation.yml ps
docker compose --env-file .env.demo -f compose.presentation.yml logs --tail=60 web
docker compose --env-file .env.demo -f compose.presentation.yml logs --tail=60 api
```

Verify `http://localhost:8100/readiness` reports `cv_ready=true`, `llm_ready=true`, and no blockers. A live Gemini response can still be affected by provider capacity; historical evaluation and saved cases remain available. The old Railway environment is not involved.

## Original version is always recoverable

Nothing in `F:\Projects\ReturnReview` needs to be edited, pulled, reset or checked out. `main` is unchanged by this presentation branch. The separate Compose project name, ports and database volume prevent interference even if both projects are running simultaneously.

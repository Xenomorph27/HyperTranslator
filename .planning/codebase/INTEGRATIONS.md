# External Integrations

**Analysis Date:** 2026-06-22

## APIs & External Services

**AI / LLM:**
- Gemini 2.5 Flash — Converts ISL word tokens into grammatical English sentences
  - SDK/Client: `google-generativeai==0.7.2` (via `genai.GenerativeModel("gemini-2.5-flash")`)
  - Auth: `GEMINI_API_KEY` env var (never hardcoded)
  - Rate limit: 60 calls/min (configured in `.agents/mcp_config.json`)
  - Max tokens per call: 100
  - Fallback: If API fails, join words with spaces and capitalize (`" ".join(words).capitalize() + "."`)
  - Implementation: `backend/models/sentence_builder.py` (to be created)

**Computer Vision:**
- MediaPipe Holistic — Extracts 543 landmarks per video frame (pose + hands + face)
  - SDK/Client: `mediapipe==0.10.9` (exact version mandatory)
  - Auth: None (runs locally, no API key)
  - Input: BGR video frames
  - Output: 2172 floats per frame (543 landmarks × 4 values each)
  - Implementation: `backend/utils/landmark_extractor.py` (to be created)

## Data Storage

**Databases:**
- None — This is a stateless API; no persistent database

**File Storage:**
- Local filesystem only
  - `data/include_raw/` — Raw INCLUDE dataset videos (gitignored)
  - `data/landmarks/` — Preprocessed `.npy` landmark arrays (gitignored)
  - `backend/weights/` — Model weights `isl_transformer.pt` + `label_map.json` (gitignored)
  - Uploaded videos: Temporary processing, not persisted

**Caching:**
- None — Model loaded once at startup via FastAPI lifespan; no request-level caching

## Authentication & Identity

**Auth Provider:**
- None — No user authentication system
- API is open (protected by CORS whitelist only)

**CORS Policy (defined in `specs/isl_translation.md`):**
- Allowed origins: `https://your-app.vercel.app`, `http://localhost:3000`
- All methods and headers allowed
- Implementation: FastAPI `CORSMiddleware` in `backend/main.py`

## Monitoring & Observability

**Error Tracking:**
- None configured — `print()` statements for logging (upgrade to `logging` module recommended)

**Logs:**
- Console output via `print()` in backend
- Gemini failures logged with `[sentence-builder]` prefix
- Model load confirmation logged at startup

## CI/CD & Deployment

**Backend Hosting:**
- Render (Python web service)
  - Build: `pip install -r requirements.txt`
  - Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
  - Free tier: Sleeps after 15 minutes of inactivity
  - Model weights: Persistent disk or downloaded from GCS at startup
  - Config: `backend/Dockerfile` (to be created)

**Frontend Hosting:**
- Vercel
  - Deploy: `npx vercel --prod` from `frontend/`
  - Auto-HTTPS: Required for webcam in production
  - Env: `NEXT_PUBLIC_BACKEND_URL` set in Vercel dashboard

**CI Pipeline:**
- None configured yet
- GitHub Actions planned for automated code review (see `code-review` skill)

## Environment Configuration

**Required env vars (backend):**
- `GEMINI_API_KEY` — Gemini API access (sync: false on Render)
- `MODEL_WEIGHTS_PATH` — Default: `./weights/isl_transformer.pt`

**Required env vars (frontend):**
- `NEXT_PUBLIC_BACKEND_URL` — Backend API endpoint

**Secrets location:**
- `backend/.env` — Local development (gitignored)
- `frontend/.env.local` — Local development (gitignored)
- Render dashboard — Production backend secrets
- Vercel dashboard — Production frontend env vars

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- Gemini API calls from `/sentence` and `/predict/video` endpoints

## Dataset Source

**INCLUDE Dataset (IIT Bombay):**
- 263 ISL sign classes, ~4,287 video clips
- Download: https://zenodo.org/record/4010759
- Placement: `data/include_raw/` (gitignored, never committed)
- Preprocessing: `training/preprocess.py` → `.npy` files in `data/landmarks/`

## MCP Server Connections

**Configured in `.agents/mcp_config.json`:**
- `filesystem` — Scoped file system access (read/write boundaries enforced)
- `github` — PR review and code inspection (cannot merge or push)
- `gemini-api` — Gemini API access for sentence building (rate-limited)

---

*Integration audit: 2026-06-22*

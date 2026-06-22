# Technology Stack

**Analysis Date:** 2026-06-22

## Languages

**Primary:**
- Python 3.11 — Backend API, ML model training, data preprocessing
- TypeScript — Frontend UI (Next.js 14 App Router)

**Secondary:**
- JavaScript — Build tooling, config files
- JSON — Configuration, label maps, eval cases
- YAML — Security policies, deployment config
- Markdown — Specs, skills, documentation

## Runtime

**Backend:**
- Python 3.11
- FastAPI ASGI server via Uvicorn

**Frontend:**
- Node.js (Next.js 14 runtime)
- React 18 (via Next.js)

**Package Managers:**
- pip + `requirements.txt` (backend)
- npm + `package.json` (frontend)
- Lockfiles: Not yet created (project is pre-implementation scaffold)

## Frameworks

**Core:**
- FastAPI 0.111.0 — Python backend REST API
- Next.js 14 (App Router) — Frontend SSR/CSR framework
- PyTorch 2.3.0 — Deep learning inference and training
- MediaPipe 0.10.9 — Holistic landmark extraction (pose + hands + face)

**Testing:**
- pytest (planned, specified in `specs/isl_translation.md`)
- Backend test directory: `backend/tests/`

**Build/Dev:**
- Uvicorn 0.30.1 — ASGI dev server
- Vercel CLI — Frontend deployment
- Docker — Backend containerization (`backend/Dockerfile`)

## Key Dependencies

**Critical (pinned versions from `specs/isl_translation.md`):**
- `mediapipe==0.10.9` — **Must not use any other version**; Holistic API breaks in newer versions
- `torch==2.3.0` — Transformer Encoder inference and training
- `fastapi==0.111.0` — API routing and validation
- `google-generativeai==0.7.2` — Gemini 2.5 Flash API client for sentence building
- `numpy==1.26.4` — Landmark array manipulation
- `opencv-python-headless==4.9.0.80` — Video frame extraction (headless for server)

**Infrastructure:**
- `uvicorn==0.30.1` — Production ASGI server
- `python-multipart==0.0.9` — File upload handling
- `python-dotenv==1.0.1` — Environment variable loading
- `scikit-learn==1.5.0` — Label encoding, train/test split

**Frontend (specified in spec, not yet in package.json):**
- `react-webcam` — 30fps webcam capture
- Next.js 14 core packages

## Configuration

**Environment:**
- Backend: `backend/.env` (gitignored, never committed)
  - `GEMINI_API_KEY` — Gemini API authentication
  - `MODEL_WEIGHTS_PATH` — Path to `isl_transformer.pt` (default: `./weights/isl_transformer.pt`)
  - `MAX_VIDEO_SIZE_MB` — Upload limit (default: 50)
- Frontend: `frontend/.env.local` (gitignored)
  - `NEXT_PUBLIC_BACKEND_URL` — Backend API URL (default: `http://localhost:8000`)

**Build:**
- `backend/Dockerfile` — Backend container build
- `backend/requirements.txt` — Python dependency pinning (to be created)
- `frontend/package.json` — Node dependency manifest (to be created)

## Platform Requirements

**Development:**
- Python 3.11+
- Node.js 18+ (for Next.js 14)
- GPU optional (CPU inference supported, training benefits from CUDA)

**Production:**
- Backend: Render (Python web service)
- Frontend: Vercel (automatic HTTPS, required for webcam in production)
- Model weights: Render persistent disk or Google Cloud Storage

---

*Stack analysis: 2026-06-22*

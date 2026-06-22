# AGENTS.md — ISL Translator Project

## Stack
- **Frontend:** Next.js 14 (App Router) → deployed on Vercel
- **Backend:** FastAPI (Python 3.11) → deployed on Render
- **ML Model 1:** MediaPipe Holistic + LSTM (PyTorch) — sign-to-word
- **ML Model 2:** Gemini API (gemini-1.5-flash) — words-to-sentence
- **Dataset:** INCLUDE ISL dataset (IIT Bombay)
- **Package manager:** pip + requirements.txt (backend), npm (frontend)

## Project Structure
```
isl-translator/
├── AGENTS.md                         ← you are here
├── specs/
│   └── isl_translation.md            ← full technical spec, read before coding
├── evals/
│   └── eval_cases.json               ← EDD eval cases, run before shipping any skill
├── security/
│   └── policies.yaml                 ← tool access rules, always enforced
├── .agents/
│   ├── mcp_config.json               ← MCP server connections
│   └── skills/
│       ├── landmark-extraction/SKILL.md
│       ├── sign-recognizer/SKILL.md
│       ├── sentence-builder/SKILL.md
│       └── code-review/SKILL.md
├── backend/
│   ├── main.py
│   ├── models/
│   │   ├── sign_recognizer.py
│   │   └── sentence_builder.py
│   ├── utils/
│   │   ├── landmark_extractor.py
│   │   └── policy_service.py
│   ├── weights/                      ← gitignored, never commit
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   └── layout.tsx
│   ├── components/
│   │   ├── WebcamCapture.tsx
│   │   ├── VideoUpload.tsx
│   │   └── TranslationDisplay.tsx
│   └── package.json
├── training/
│   ├── train.py
│   ├── preprocess.py
│   └── evaluate.py
└── data/                             ← gitignored, never commit
    └── README.md
```

## Conventions
- Python: snake_case, type hints on every function, Google-style docstrings
- TypeScript: camelCase, functional components only, no class components
- All API keys and secrets go in `.env` files — NEVER hardcoded
- Every backend route must have a corresponding test in `backend/tests/`
- Commit messages: `feat:`, `fix:`, `train:`, `docs:`, `eval:` prefixes

## Hard Rules (Never Do These)
- NEVER hardcode API keys, model paths, or dataset paths — use env variables
- NEVER commit `weights/` or `data/` folders to git
- NEVER skip input validation on FastAPI routes
- NEVER use `any` type in TypeScript
- NEVER run training code inside the FastAPI server
- NEVER modify test files and implementation files in the same commit
- NEVER call Gemini API with an empty word list
- NEVER load model weights inside a request handler — load once at startup
- NEVER use mediapipe version other than 0.10.9

## Environment Variables
```bash
# backend/.env
GEMINI_API_KEY=your_key_here
MODEL_WEIGHTS_PATH=./weights/isl_lstm.pt
MAX_VIDEO_SIZE_MB=50

# frontend/.env.local
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

## Skills — What to Use When
| Task | Skill to load |
|---|---|
| Preprocess video → landmarks | `landmark-extraction` |
| Run sign inference | `sign-recognizer` |
| Convert words → sentence | `sentence-builder` |
| Review a PR | `code-review` |

## Workflow
1. Read `specs/isl_translation.md` before writing any code
2. Check `evals/eval_cases.json` — find the relevant eval cases for what you're building
3. Write failing tests first, then implement
4. Show me a plan before changing more than 2 files at once
5. After implementing any skill, run its eval cases and confirm they pass
6. For ML components: verify output shapes before wiring to API

## Security
- All tool calls go through `security/policies.yaml` — check it before taking any action
- MCP servers configured in `.agents/mcp_config.json`
- Agent cannot read `.env` files, `weights/`, or `data/`
- High-risk actions (deploy, DB changes) require my explicit approval

## Known Gotchas
- MediaPipe requires exactly `mediapipe==0.10.9`
- INCLUDE dataset videos → extract to `.npy` before training (do not train on raw video)
- Render free tier sleeps after 15 min — frontend must handle cold start with retry logic
- Next.js webcam needs `https` in production — Vercel provides this automatically
- Landmark order must always be: pose (33) → left hand (21) → right hand (21) → face (468)
- `torch.no_grad()` is mandatory during inference — missing it causes memory leaks

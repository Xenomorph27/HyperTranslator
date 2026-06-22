# Codebase Structure

**Analysis Date:** 2026-06-22

## Directory Layout

```
HyperTranslator/
├── .agents/                    # Agent skill definitions and MCP config
│   ├── mcp_config.json         # MCP server connections (filesystem, github, gemini)
│   └── skills/                 # 4 project-specific skills
│       ├── code-review/SKILL.md
│       ├── landmark-extraction/SKILL.md
│       ├── sentence-builder/SKILL.md
│       └── sign-recognizer/SKILL.md
├── .claude/                    # Claude/GSD workflow tooling
│   ├── agents/                 # GSD subagent definitions
│   ├── get-shit-done/          # GSD workflow engine
│   ├── hooks/                  # GSD hooks
│   ├── skills/                 # GSD skills
│   ├── settings.json           # GSD settings
│   └── gsd-file-manifest.json  # GSD file integrity manifest
├── .planning/                  # GSD planning artifacts (this directory)
│   └── codebase/               # Codebase mapping documents
├── backend/                    # FastAPI Python backend (TO BE CREATED)
│   ├── main.py                 # App entry point, routes, CORS, lifespan
│   ├── models/                 # ML model wrappers
│   │   ├── sign_recognizer.py  # ISLTransformer loading and inference
│   │   └── sentence_builder.py # Gemini API sentence generation
│   ├── utils/                  # Utilities
│   │   ├── landmark_extractor.py  # MediaPipe Holistic processing
│   │   └── policy_service.py   # Security policy enforcement
│   ├── weights/                # Model weights (GITIGNORED)
│   ├── tests/                  # Backend tests
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile              # Container build
├── frontend/                   # Next.js 14 frontend (TO BE CREATED)
│   ├── app/
│   │   ├── page.tsx            # Main page
│   │   └── layout.tsx          # Root layout
│   ├── components/
│   │   ├── WebcamCapture.tsx    # Live webcam + landmark overlay
│   │   ├── VideoUpload.tsx     # Drag-drop video upload
│   │   └── TranslationDisplay.tsx  # Word bubbles + sentence display
│   └── package.json            # Node dependencies
├── training/                   # Offline ML training (TO BE CREATED)
│   ├── preprocess.py           # Video → .npy landmark extraction
│   ├── train.py                # ISLTransformer training loop
│   └── evaluate.py             # Model evaluation
├── data/                       # Dataset files (GITIGNORED)
│   └── README.md               # Dataset download instructions
├── specs/
│   └── isl_translation.md      # Full technical specification (434 lines)
├── evals/
│   └── eval_cases.json         # 13 BDD-style eval cases (248 lines)
├── security/
│   └── policies.yaml           # Security policies (88 lines)
├── AGENTS.md                   # Project conventions and hard rules
└── .gitignore                  # Comprehensive Python + Node ignores
```

## Directory Purposes

**`backend/`:**
- Purpose: FastAPI REST API server for sign prediction and sentence building
- Contains: Python modules for API routes, ML inference, utilities
- Key files: `main.py` (entry point), `models/sign_recognizer.py` (inference), `models/sentence_builder.py` (Gemini)
- Status: **Not yet created** — defined in spec, to be built in Phase 1

**`frontend/`:**
- Purpose: Next.js 14 App Router client for webcam capture and translation display
- Contains: React components (TSX), Next.js pages, layouts
- Key files: `app/page.tsx` (main page), `components/WebcamCapture.tsx` (camera), `components/TranslationDisplay.tsx` (output)
- Status: **Not yet created** — defined in spec, to be built in Phase 1

**`training/`:**
- Purpose: Offline dataset preprocessing and Transformer model training
- Contains: Python scripts for data prep and training loop
- Key files: `preprocess.py` (video → npy), `train.py` (model training)
- Status: **Not yet created** — to be built in Phases 2–4

**`specs/`:**
- Purpose: Technical specifications and project documentation
- Contains: Full project spec with architecture, model details, BDD scenarios
- Key files: `isl_translation.md` (434 lines, the source of truth)

**`evals/`:**
- Purpose: Evaluation-driven development test cases
- Contains: JSON eval cases for all 4 skills
- Key files: `eval_cases.json` (13 cases covering landmark extraction, sign recognition, sentence building, code review)

**`security/`:**
- Purpose: Security policies governing agent and API behavior
- Contains: YAML policy definitions (roles, blocked tools, secret patterns)
- Key files: `policies.yaml` (88 lines)

**`.agents/skills/`:**
- Purpose: Skill definitions for the 4 core project capabilities
- Contains: SKILL.md files with workflow instructions, code templates, anti-patterns
- Key files: `landmark-extraction/SKILL.md`, `sign-recognizer/SKILL.md`, `sentence-builder/SKILL.md`, `code-review/SKILL.md`

**`data/` (gitignored):**
- Purpose: Dataset storage (raw videos and processed landmarks)
- Contains: `include_raw/` (INCLUDE dataset videos), `landmarks/` (preprocessed .npy files)
- Generated: Yes (via download + preprocessing)
- Committed: **Never** — gitignored

**`backend/weights/` (gitignored):**
- Purpose: Trained model weights and label maps
- Contains: `isl_transformer.pt`, `label_map.json`
- Generated: Yes (via training)
- Committed: **Never** — gitignored

## Key File Locations

**Entry Points:**
- `backend/main.py`: FastAPI application entry, `uvicorn main:app`
- `frontend/app/page.tsx`: Next.js main page
- `training/train.py`: Training script entry, `python train.py`
- `training/preprocess.py`: Preprocessing entry, `python preprocess.py`

**Configuration:**
- `AGENTS.md`: Project conventions, hard rules, workflow (root level)
- `specs/isl_translation.md`: Full technical spec, architecture, BDD scenarios
- `security/policies.yaml`: Security policies, roles, blocked patterns
- `.agents/mcp_config.json`: MCP server connections
- `backend/.env`: Backend secrets (gitignored)
- `frontend/.env.local`: Frontend config (gitignored)

**Core Logic:**
- `backend/models/sign_recognizer.py`: ISLTransformer model loading + `predict_sign()`
- `backend/models/sentence_builder.py`: Gemini API + `build_sentence()`
- `backend/utils/landmark_extractor.py`: MediaPipe Holistic processing
- `training/train.py`: Full training loop with augmentation

**Testing:**
- `backend/tests/`: Backend test directory
- `evals/eval_cases.json`: BDD eval cases for all skills

## Naming Conventions

**Files:**
- Python: `snake_case.py` (e.g., `sign_recognizer.py`, `landmark_extractor.py`)
- TypeScript: `PascalCase.tsx` for components (e.g., `WebcamCapture.tsx`)
- Config: `lowercase.ext` (e.g., `requirements.txt`, `policies.yaml`)
- Skills: `SKILL.md` (uppercase) inside kebab-case directories

**Directories:**
- Python packages: `snake_case/` (e.g., `models/`, `utils/`)
- TypeScript: `lowercase/` (e.g., `components/`, `app/`)
- Spec/config dirs: `lowercase/` (e.g., `specs/`, `security/`, `evals/`)

## Where to Add New Code

**New Backend Route:**
- Add route in: `backend/main.py`
- Add logic in: `backend/models/` or `backend/utils/`
- Add test in: `backend/tests/test_<module>.py`

**New Frontend Component:**
- Add component: `frontend/components/<ComponentName>.tsx`
- Use in page: `frontend/app/page.tsx`
- Functional components only, no class components

**New ML Feature:**
- Training code: `training/`
- Inference code: `backend/models/`
- Never mix training and inference in the same file

**New Utility:**
- Backend utility: `backend/utils/<utility_name>.py`
- Shared helpers stay within their layer

**New Skill:**
- Skill definition: `.agents/skills/<skill-name>/SKILL.md`
- Eval cases: `evals/eval_cases.json` (append new cases)

## Special Directories

**`backend/weights/`:**
- Purpose: Trained model checkpoints and label maps
- Generated: Yes (by `training/train.py`)
- Committed: **No** — gitignored, uploaded to Render persistent disk

**`data/`:**
- Purpose: Raw dataset and preprocessed landmarks
- Generated: Yes (download + `training/preprocess.py`)
- Committed: **No** — gitignored, too large for git

**`.planning/`:**
- Purpose: GSD planning artifacts and codebase maps
- Generated: Yes (by `/gsd-map-codebase`)
- Committed: Yes — useful reference for future sessions

---

*Structure analysis: 2026-06-22*

# Codebase Concerns

**Analysis Date:** 2026-06-22

## Tech Debt

**No implementation code exists yet:**
- Issue: The entire project is currently a specification scaffold — `AGENTS.md`, `specs/`, `evals/`, `security/`, and skill definitions exist, but no actual `backend/`, `frontend/`, or `training/` source code has been written
- Files: `specs/isl_translation.md`, `AGENTS.md`
- Impact: Zero functionality — the project cannot run, test, or deploy
- Fix approach: Follow the 9-phase build order in `specs/isl_translation.md` starting with Phase 1 (project scaffold)

**MCP config references incorrect Gemini model:**
- Issue: `.agents/mcp_config.json` restricts to `gemini-1.5-flash` (line 72) but `specs/isl_translation.md` specifies `gemini-2.5-flash` (line 151). The sentence-builder skill also references `gemini-1.5-flash` (line 79)
- Files: `.agents/mcp_config.json`, `.agents/skills/sentence-builder/SKILL.md`
- Impact: Model mismatch between spec and skill definitions could cause confusion during implementation
- Fix approach: Align all references to `gemini-2.5-flash` per the spec, or explicitly document which model to use

## Known Bugs

**No bugs (no code exists):**
- The project is pre-implementation, so no runtime bugs exist yet
- Potential issues are documented as "Known Gotchas" in `AGENTS.md`

## Security Considerations

**API key exposure risk:**
- Risk: Gemini API key could be hardcoded during development
- Files: `backend/models/sentence_builder.py` (to be created)
- Current mitigation: `security/policies.yaml` defines `blocked_secret_patterns` (line 65–69) to catch hardcoded keys
- Recommendations: Enforce secret scanning in CI, use pre-commit hooks

**CORS misconfiguration risk:**
- Risk: Setting `allow_origins=["*"]` would expose API to any domain
- Files: `backend/main.py` (to be created)
- Current mitigation: Spec defines explicit origin whitelist; `security/policies.yaml` requires human approval for CORS changes
- Recommendations: Test CORS config in deployment checklist

**No authentication on API:**
- Risk: API endpoints are publicly accessible (protected only by CORS)
- Files: `backend/main.py` (to be created)
- Current mitigation: CORS whitelist limits browser-based access
- Recommendations: Consider API key or rate limiting for production; acceptable for MVP

**Model weights in git risk:**
- Risk: Large `.pt` files could accidentally be committed
- Files: `.gitignore` (already blocks `*.pt`, `*.pth`, `backend/weights/`)
- Current mitigation: Gitignore rules in place
- Recommendations: Add pre-commit hook to verify no weights are staged

**Protected paths enforced:**
- `security/policies.yaml` blocks agent access to: `backend/.env`, `frontend/.env.local`, `backend/weights/`, `.git/`
- MCP config blocks: `backend/.env`, `frontend/.env.local`, `backend/weights/`, `.git/`

## Performance Bottlenecks

**Render free tier cold start:**
- Problem: Render free tier sleeps after 15 minutes of inactivity, causing 30–60 second cold starts
- Files: `frontend/components/WebcamCapture.tsx` (to be created)
- Cause: Free tier spin-down policy
- Improvement path: Frontend must implement retry logic (3-second intervals for 30 seconds) with "Warming up server..." UX. Documented as BDD Scenario 4 in spec

**MediaPipe landmark extraction speed:**
- Problem: Processing 30 frames through MediaPipe Holistic on CPU can be slow
- Files: `backend/utils/landmark_extractor.py` (to be created)
- Cause: Face mesh (468 landmarks) is computationally expensive
- Improvement path: Consider client-side landmark extraction (MediaPipe JS) to offload from server

**Model inference on CPU:**
- Problem: Target is ≤100ms per sequence on CPU — needs verification after training
- Files: `backend/models/sign_recognizer.py` (to be created)
- Cause: Transformer attention scales quadratically with sequence length (31 tokens is small, should be fine)
- Improvement path: If too slow, consider ONNX export or TorchScript optimization

## Fragile Areas

**Landmark order dependency:**
- Files: `backend/utils/landmark_extractor.py` (to be created), `training/preprocess.py` (to be created)
- Why fragile: Concatenation order must be exactly: pose (33) → left hand (21) → right hand (21) → face (468). Wrong order silently produces incorrect predictions
- Safe modification: Never change concatenation order without retraining the model
- Test coverage: Add shape assertion tests and verify landmark order in eval cases

**MediaPipe version pinning:**
- Files: `backend/requirements.txt` (to be created)
- Why fragile: `mediapipe==0.10.9` is mandatory — the Holistic API changed in later versions
- Safe modification: Never upgrade without testing full pipeline
- Test coverage: Pin in requirements.txt and add version check in CI

**Confidence threshold coupling:**
- Files: `backend/models/sign_recognizer.py` (to be created), `frontend/components/TranslationDisplay.tsx` (to be created)
- Why fragile: `CONFIDENCE_THRESHOLD = 0.85` in backend must match frontend's expectation of when words appear
- Safe modification: Make threshold configurable via env var
- Test coverage: Eval case `sign_recognizer_002` covers low confidence rejection

## Scaling Limits

**Concurrent requests:**
- Current capacity: Single-threaded FastAPI with model loaded in memory
- Limit: One inference at a time (PyTorch model is not thread-safe without `torch.no_grad()`)
- Scaling path: Use Uvicorn workers or move to async inference with request queuing

**Video upload size:**
- Current capacity: 50MB limit per upload
- Limit: Render free tier has limited disk and memory
- Scaling path: Consider chunked upload or client-side preprocessing

## Dependencies at Risk

**MediaPipe 0.10.9:**
- Risk: Pinned to a specific version; newer versions break the Holistic API
- Impact: Cannot upgrade without rewriting landmark extraction
- Migration plan: v2 could switch to MediaPipe Tasks API (newer, maintained) or client-side MediaPipe JS

**Google Generative AI SDK 0.7.2:**
- Risk: SDK is rapidly evolving; API surface may change
- Impact: `build_sentence()` could break on SDK upgrade
- Migration plan: Pin version strictly; test before upgrading

**Render Free Tier:**
- Risk: Cold starts, limited memory, no persistent disk (unless paid)
- Impact: Poor user experience on first request
- Migration plan: Upgrade to paid tier or switch to Railway/Fly.io

## Missing Critical Features

**No backend or frontend code:**
- Problem: The entire application code is missing — only specs and agent skills exist
- Blocks: Nothing can be tested, deployed, or demonstrated
- Priority: **Critical** — must be built following the 9-phase plan

**No CI/CD pipeline:**
- Problem: No automated testing, linting, or deployment pipeline
- Blocks: Cannot catch regressions, enforce code quality, or auto-deploy
- Priority: Medium — set up after Phase 1 scaffold

**No error monitoring:**
- Problem: No Sentry, DataDog, or structured logging configured
- Blocks: Cannot detect production errors or performance issues
- Priority: Low — add before production launch

## Test Coverage Gaps

**100% gap — no tests exist:**
- What's not tested: Everything (no code exists yet)
- Files: `backend/tests/` (empty or non-existent)
- Risk: Cannot verify any functionality
- Priority: **High** — write tests alongside implementation per "write failing tests first" workflow

**Eval cases defined but not runnable:**
- What's not tested: 13 eval cases in `evals/eval_cases.json` define expected behavior but cannot be executed yet
- Files: `evals/eval_cases.json`
- Risk: Eval-driven development workflow is blocked until implementation begins
- Priority: High — implement eval runner or translate to pytest

---

*Concerns audit: 2026-06-22*

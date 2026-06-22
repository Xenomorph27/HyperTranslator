# Coding Conventions

**Analysis Date:** 2026-06-22

## Naming Patterns

**Files:**
- Python: `snake_case.py` — e.g., `sign_recognizer.py`, `landmark_extractor.py`, `policy_service.py`
- TypeScript: `PascalCase.tsx` for components — e.g., `WebcamCapture.tsx`, `VideoUpload.tsx`, `TranslationDisplay.tsx`
- Config: `lowercase` with appropriate extension — e.g., `requirements.txt`, `policies.yaml`
- Test files: `test_<module>.py` — follow pytest discovery conventions

**Functions:**
- Python: `snake_case` with type hints on every function — e.g., `def predict_sign(landmark_sequence: np.ndarray) -> dict:`
- TypeScript: `camelCase` — e.g., `handleSubmit`, `fetchPrediction`

**Variables:**
- Python: `snake_case` — e.g., `word_buffer`, `landmark_sequence`, `confidence_threshold`
- TypeScript: `camelCase` — e.g., `isRecording`, `wordBuffer`
- Constants: `UPPER_SNAKE_CASE` — e.g., `CONFIDENCE_THRESHOLD = 0.85`, `SILENCE_THRESHOLD = 2.0`

**Types:**
- Python: Google-style docstrings with type hints
- TypeScript: Never use `any` type — always explicit types
- Components: Functional components only, no class components

## Code Style

**Python Formatting:**
- Use type hints on every function (enforced by project rules)
- Google-style docstrings on all public functions
- Module-level globals prefixed with underscore for private (`_model`, `_label_map`)
- No linting/formatting tools configured yet (recommend: `ruff`, `black`)

**TypeScript Formatting:**
- No formatter configured yet (recommend: `prettier`, `eslint`)
- Functional components only — class components are banned
- Never use `any` type — hard rule from `AGENTS.md`

**Linting:**
- No linting tools configured in the current scaffold
- Recommend adding: `ruff` (Python), `eslint` + `prettier` (TypeScript)

## Import Organization

**Python:**
1. Standard library (`import os`, `import json`, `from pathlib import Path`)
2. Third-party (`import torch`, `import numpy as np`, `import mediapipe`)
3. Local project (`from backend.models.sign_recognizer import load_model`)

**TypeScript (planned):**
1. React/Next.js imports
2. Third-party libraries
3. Local components and utilities

**Path Aliases:**
- None configured — use relative imports

## Error Handling

**Patterns:**
- Use `try/except` with graceful fallback for all external API calls (Gemini)
- Never let external service failures crash the API — always provide a fallback response
- Use `ValueError` for input validation failures (wrong shape, empty list)
- Use `RuntimeError` for system state errors (model not loaded)
- FastAPI returns HTTP 422 for validation errors with clear error messages
- Log errors but never expose internal details to users

**Example — Gemini API fallback:**
```python
try:
    response = model.generate_content(prompt)
    return response.text.strip()
except Exception as e:
    fallback = " ".join(words).capitalize() + "."
    print(f"[sentence-builder] Gemini failed: {e}. Using fallback: {fallback}")
    return fallback
```

## Logging

**Framework:** `print()` (console output)

**Patterns:**
- Use bracketed prefix for component identification: `[sentence-builder]`, `[sign-recognizer]`
- Log model loading confirmation at startup
- Log Gemini failures with error details
- Do not use `print()` in production — upgrade to `logging` module (listed as improvement)

## Comments

**When to Comment:**
- Explain WHY, not WHAT (the code should be self-documenting for WHAT)
- Mark critical constraints: `# CRITICAL: sets dropout to 0 for inference`
- Mark version constraints: `# IMPORTANT: use this exact version — mediapipe==0.10.9`
- Mark deliberate choices: `# Newer versions break the Holistic API`

**Docstrings (Python):**
- Use Google-style on all public functions
- Include `Args:`, `Returns:`, `Raises:` sections

**Example:**
```python
def predict_sign(landmark_sequence: np.ndarray) -> dict:
    """
    Predict ISL sign from landmark sequence.

    Args:
        landmark_sequence: numpy array shape (30, 2172)

    Returns:
        {"word": str | None, "confidence": float}

    Raises:
        RuntimeError: if model not loaded
        ValueError: if input shape is wrong
    """
```

## Function Design

**Size:** Functions should be focused and concise; no specific line limit but split at 50+ lines
**Parameters:** Use type hints on all parameters; prefer structured types over loose dicts
**Return Values:** Return typed dictionaries with clear key names; include confidence scores even when prediction is null

## Module Design

**Exports:** Each module exposes clear public functions (no barrel files in Python)
- `sign_recognizer.py` → `load_model()`, `predict_sign()`
- `sentence_builder.py` → `build_sentence()`
- `landmark_extractor.py` → `extract_landmarks_from_frame()`

**Singleton Pattern:** Use module-level globals for shared state (model weights loaded once at startup)

## Git Conventions

**Commit Messages (prefix required):**
- `feat:` — New features
- `fix:` — Bug fixes
- `train:` — Training-related changes
- `docs:` — Documentation changes
- `eval:` — Evaluation and testing changes

**Hard rules:**
- Never commit `weights/` or `data/` folders
- Never modify test files and implementation files in the same commit
- Never hardcode API keys, model paths, or dataset paths

## Environment Variables

**Always use env vars for:**
- API keys (`GEMINI_API_KEY`)
- File paths (`MODEL_WEIGHTS_PATH`)
- Configuration values (`MAX_VIDEO_SIZE_MB`)

**Never hardcode:**
- API keys, tokens, passwords
- Model weight paths
- Dataset paths
- Backend URLs in frontend

---

*Convention analysis: 2026-06-22*

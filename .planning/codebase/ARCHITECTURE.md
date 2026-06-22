# Architecture

**Analysis Date:** 2026-06-22

## Pattern Overview

**Overall:** Client-Server with ML Pipeline

**Key Characteristics:**
- Stateless REST API backend (FastAPI) serving ML predictions
- Two-model inference pipeline: Transformer → Gemini LLM
- Frontend handles webcam capture and frame batching client-side
- Model loaded once at startup (lifespan pattern), shared across requests
- Offline training pipeline completely separated from serving

## Layers

**Presentation Layer (Frontend):**
- Purpose: Webcam capture, video upload, translation display
- Location: `frontend/app/`, `frontend/components/`
- Contains: React components, Next.js pages, client-side frame batching
- Depends on: Backend API endpoints
- Used by: End users via browser

**API Layer (Backend):**
- Purpose: HTTP endpoints for sign prediction, sentence building, health checks
- Location: `backend/main.py`
- Contains: FastAPI routes, CORS config, request validation, lifespan startup
- Depends on: Models layer, Utils layer
- Used by: Frontend via REST calls

**Models Layer (Backend):**
- Purpose: ML inference (sign recognition) and LLM calls (sentence building)
- Location: `backend/models/`
  - `backend/models/sign_recognizer.py` — ISLTransformer inference
  - `backend/models/sentence_builder.py` — Gemini API sentence generation
- Contains: Model loading, prediction functions, confidence thresholding
- Depends on: PyTorch, google-generativeai, model weights on disk
- Used by: API layer routes

**Utils Layer (Backend):**
- Purpose: Supporting utilities (landmark extraction, policy enforcement)
- Location: `backend/utils/`
  - `backend/utils/landmark_extractor.py` — MediaPipe Holistic processing
  - `backend/utils/policy_service.py` — Security policy enforcement
- Contains: Video processing, policy checking
- Depends on: MediaPipe, OpenCV
- Used by: API layer (for video upload endpoint)

**Training Layer (Offline):**
- Purpose: Dataset preprocessing and model training (never runs in production)
- Location: `training/`
  - `training/preprocess.py` — Video → .npy landmark extraction
  - `training/train.py` — ISLTransformer training loop
  - `training/evaluate.py` — Model evaluation
- Contains: Data loading, augmentation, training loop, checkpoint saving
- Depends on: PyTorch, NumPy, scikit-learn, MediaPipe
- Used by: Developers offline only

## Data Flow

**Real-time Webcam Translation:**

1. Browser captures 30 frames at 30fps via `react-webcam` (`frontend/components/WebcamCapture.tsx`)
2. Client extracts landmarks client-side OR sends frame batch to backend
3. POST to `/predict/frame-sequence` with `(30, 2172)` landmark array + session_id
4. `sign_recognizer.predict_sign()` runs ISLTransformer inference with `torch.no_grad()`
5. If confidence ≥ 0.85: word returned to client, added to word buffer
6. If confidence < 0.85: null word returned, not added to buffer
7. After 2 seconds of silence: word buffer flushed
8. POST to `/sentence` with accumulated words
9. `sentence_builder.build_sentence()` calls Gemini 2.5 Flash
10. Grammatical sentence returned and displayed

**Video Upload Translation:**

1. User uploads `.mp4`/`.webm`/`.mov` (max 50MB) via `frontend/components/VideoUpload.tsx`
2. POST to `/predict/video` as multipart file upload
3. Backend extracts landmarks using `landmark_extractor.py` (MediaPipe Holistic)
4. Landmarks split into 30-frame sequences
5. Each sequence fed through `sign_recognizer.predict_sign()`
6. All predicted words collected
7. Words sent to `sentence_builder.build_sentence()` (Gemini)
8. Full sentence + word list + timing returned to frontend

**Offline Training Pipeline:**

1. Download INCLUDE dataset → `data/include_raw/`
2. Run `training/preprocess.py` → `.npy` files saved to `data/landmarks/`
3. Run `training/train.py` → Best checkpoint saved to `backend/weights/isl_transformer.pt`
4. Label map saved to `backend/weights/label_map.json`
5. Upload weights to Render persistent disk for production

**State Management:**
- Backend: Stateless (no sessions, no database)
- Model state: Global singleton loaded at startup (`_model`, `_label_map` globals in `sign_recognizer.py`)
- Word buffer: Client-side management with 2-second silence threshold
- Session ID: Client-generated, passed through for correlation only

## Key Abstractions

**ISLTransformer:**
- Purpose: 4-layer Transformer Encoder for sign classification
- Examples: `backend/models/sign_recognizer.py`, `training/train.py`
- Pattern: CLS token prepended → positional encoding → self-attention → classification head
- Input: `(batch, 30, 2172)` → Output: `(batch, 263)` class logits

**WordBuffer:**
- Purpose: Accumulates predicted words, flushes after silence
- Examples: `backend/models/sentence_builder.py` (WordBuffer class)
- Pattern: Timer-based flush with configurable silence threshold (2.0 seconds)

**Landmark Sequence:**
- Purpose: Standardized representation of a sign gesture
- Pattern: 30 frames × 2172 floats = `(30, 2172)` numpy array
- Order: pose (33×4) + left_hand (21×4) + right_hand (21×4) + face (468×4)

## Entry Points

**Backend API:**
- Location: `backend/main.py`
- Triggers: HTTP requests from frontend
- Responsibilities: Route dispatch, CORS, model loading at startup
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Frontend App:**
- Location: `frontend/app/page.tsx`
- Triggers: User browser navigation
- Responsibilities: Camera access, UI rendering, API calls

**Training Entry:**
- Location: `training/train.py`
- Triggers: Developer CLI execution
- Responsibilities: Load data, train model, save checkpoint

**Preprocessing Entry:**
- Location: `training/preprocess.py`
- Triggers: Developer CLI execution
- Responsibilities: Convert videos to landmark arrays

## Error Handling

**Strategy:** Graceful degradation with fallbacks

**Patterns:**
- Gemini API failure → Fallback to joined words: `" ".join(words).capitalize() + "."` (never crash)
- Low confidence prediction → Return `null` word with confidence score (don't add to buffer)
- Model not loaded → `RuntimeError` with clear message
- Wrong input shape → `ValueError` with expected vs actual shape
- Cold start on Render → Frontend auto-retries every 3 seconds for 30 seconds

## Cross-Cutting Concerns

**Logging:** Console `print()` statements (planned upgrade to `logging` module)
**Validation:** FastAPI Pydantic models for request validation; shape assertions for numpy arrays
**Authentication:** None — open API protected by CORS whitelist only
**Security:** Policy enforcement via `security/policies.yaml` and `backend/utils/policy_service.py`

---

*Architecture analysis: 2026-06-22*

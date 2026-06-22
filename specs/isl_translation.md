# ISL Translator — Project Spec
**Version:** 2.0.0
**Last updated:** June 2026
**Stack:** FastAPI + Next.js + MediaPipe + PyTorch Transformer + Gemini 2.5 Flash

---

## What We're Building

A real-time Indian Sign Language (ISL) to English text translator that:
1. Takes webcam input or uploaded video
2. Detects and classifies individual ISL signs into words (Model 1 — Transformer)
3. Strings those words into grammatically correct English sentences (Model 2 — Gemini 2.5 Flash)
4. Displays the translation live on screen

---

## Architecture

```
[Webcam / Video File]
        ↓
[MediaPipe Holistic] ← extracts 543 landmarks per frame (hands + pose + face)
        ↓
[Landmark Array (30, 2172)]
        ↓
[Transformer Encoder] ← all 30 frames attend to each other simultaneously
        ↓                  target accuracy: 92–94%
[Predicted Sign Word + Confidence]
        ↓
[Word Buffer] ← accumulates words, flushes after 2s of silence
        ↓
[Gemini 2.5 Flash API] ← converts word list to grammatical English sentence
        ↓
[Display on screen]
```

---

## Model 1 — Sign Recognizer (Transformer Encoder)

### Why Transformer over LSTM
LSTM processes frames one at a time and forgets early frames by the end.
The Transformer reads all 30 frames simultaneously — every frame can attend
to every other frame — making it far better at capturing the full arc of a sign.

### Input
- 30 consecutive video frames (~1 second at 30fps)
- Each frame: 543 landmarks × 4 values (x, y, z, visibility) = 2172 floats
- Shape per sequence: `(30, 2172)`

### Architecture
```
Input (30, 2172)
    ↓
Linear Projection → (30, 256)       # project landmarks into model space
    ↓
Prepend CLS token → (31, 256)       # learnable summary token
    ↓
Positional Encoding → (31, 256)     # inject frame-order information
    ↓
Transformer Encoder × 4 layers      # each layer: self-attention + feedforward
  - d_model: 256
  - nhead: 8 attention heads
  - dim_feedforward: 512
  - dropout: 0.1
  - Pre-LayerNorm (stable training)
    ↓
CLS token output → (256,)           # sequence summary
    ↓
LayerNorm → Linear(256→128) → GELU → Dropout → Linear(128→263)
    ↓
Softmax → predicted sign class
```

### Output
- Predicted sign label (string, e.g. `"namaste"`, `"hello"`, `"thank_you"`)
- Confidence score (float 0–1)
- Only emit prediction if confidence ≥ 0.85

### Training config
```
optimizer:     AdamW (lr=1e-4, weight_decay=0.01)
scheduler:     CosineAnnealingLR (T_max=60)
loss:          CrossEntropyLoss (label_smoothing=0.1)
grad_clip:     1.0
epochs:        60
batch_size:    32
augmentation:  time shift, gaussian noise, horizontal flip (swap hands)
```

### Dataset
- **INCLUDE dataset** by IIT Bombay — 263 ISL sign classes, ~4,287 video clips
- Download: https://zenodo.org/record/4010759
- Place raw videos in `data/include_raw/`
- Run `training/preprocess.py` → saves `.npy` files to `data/landmarks/`

### Training commands
```bash
cd training
python preprocess.py --data_dir ../data/include_raw --out_dir ../data/landmarks
python train.py --data_dir ../data/landmarks --epochs 60 --batch_size 32
# Saves weights to ../backend/weights/isl_transformer.pt
# Saves label map to ../backend/weights/label_map.json
```

### Evaluation targets
- Validation accuracy ≥ 92%
- Inference time per sequence ≤ 100ms on CPU
- If accuracy < 85% after 60 epochs: check class balance, data quality, landmark extraction

### V2 upgrade path (do after v1 ships)
Upgrade to SignFormer-GCN for ~96% accuracy:
- Replace Linear Projection with a Graph Convolutional Network
- Model joint connections explicitly (wrist → elbow → shoulder)
- Add RGB frame stream as second input
- Keep Transformer Encoder stack unchanged

---

## Model 2 — Sentence Builder (Gemini 2.5 Flash)

### What it does
Takes a list of raw sign words and returns a grammatically correct English sentence.
ISL grammar differs from English — it omits articles and verb-to-be — so an LLM
is the right tool for natural sentence reconstruction.

### Implementation
```python
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

PROMPT_TEMPLATE = """You are a helpful assistant converting Indian Sign Language word tokens to natural English.

The signer produced these words in order: {words}

Convert this into one natural, grammatically correct English sentence.
Rules:
- Return ONLY the sentence, no explanation, no quotes
- Keep the original meaning of all words
- Fix grammar naturally (ISL omits articles and verb-to-be)
- Maximum one sentence"""

def build_sentence(words: list[str]) -> str:
    if not words:
        raise ValueError("Word list is empty.")

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            PROMPT_TEMPLATE.format(words=', '.join(words)),
            generation_config=genai.types.GenerationConfig(max_output_tokens=100)
        )
        return response.text.strip()
    except Exception as e:
        fallback = " ".join(words).capitalize() + "."
        print(f"[sentence-builder] Gemini failed: {e}. Fallback: {fallback}")
        return fallback
```

### Word Buffer Logic
```python
SILENCE_THRESHOLD = 2.0  # seconds

if time_since_last_sign > SILENCE_THRESHOLD and len(word_buffer) > 0:
    sentence = build_sentence(word_buffer)
    word_buffer.clear()
    display(sentence)
```

---

## Backend — FastAPI

### Startup
```python
from contextlib import asynccontextmanager
from backend.models.sign_recognizer import load_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()   # load Transformer weights once at startup
    yield

app = FastAPI(title="ISL Translator API", version="2.0.0", lifespan=lifespan)
```

### Routes

#### `GET /health`
```json
{ "status": "ok", "model": "isl_transformer_v2", "classes": 263 }
```

#### `POST /predict/frame-sequence`
**Input:**
```json
{
  "frames": [[2172 floats] × 30],
  "session_id": "string"
}
```
**Output:**
```json
{
  "word": "namaste",
  "confidence": 0.96,
  "session_id": "string"
}
```

#### `POST /predict/video`
**Input:** multipart file upload (`.mp4`, `.webm`, `.mov`), max 50MB
**Output:**
```json
{
  "words": ["i", "am", "good"],
  "sentence": "I am doing well.",
  "processing_time_ms": 1240
}
```

#### `POST /sentence`
**Input:** `{ "words": ["i", "am", "good"] }`
**Output:** `{ "sentence": "I am doing well." }`

### CORS
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-app.vercel.app", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Requirements
```
fastapi==0.111.0
uvicorn==0.30.1
mediapipe==0.10.9
torch==2.3.0
numpy==1.26.4
opencv-python-headless==4.9.0.80
google-generativeai==0.7.2
python-multipart==0.0.9
python-dotenv==1.0.1
scikit-learn==1.5.0
```

---

## Frontend — Next.js 14

### Components

#### `WebcamCapture.tsx`
- `react-webcam` for video capture at 30fps
- Sends batches of 30 frames to `/predict/frame-sequence` every second
- Canvas overlay showing MediaPipe landmark dots live

#### `VideoUpload.tsx`
- Drag-and-drop or click-to-upload
- Accepts `.mp4`, `.webm`, `.mov`, max 50MB
- Progress bar during upload and processing
- Calls `/predict/video`

#### `TranslationDisplay.tsx`
- Word bubbles row — each detected word appears as a pill
- Sentence box below — final sentence in large text
- Copy button, Clear button
- Animates new words appearing

### UI States
1. **Idle** — camera permission prompt
2. **Detecting** — live feed + landmark overlay + word bubbles
3. **Translating** — spinner while Gemini builds sentence
4. **Result** — full sentence displayed
5. **Error** — camera denied / backend down / file too large
6. **Cold start** — "Warming up server..." with auto-retry every 3s for 30s

---

## Deployment

### Backend → Render
```yaml
services:
  - type: web
    name: isl-translator-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GEMINI_API_KEY
        sync: false
      - key: MODEL_WEIGHTS_PATH
        value: ./weights/isl_transformer.pt
```

**Important:** Upload `isl_transformer.pt` and `label_map.json` to Render as a
persistent disk or store in Google Cloud Storage and download at startup.

### Frontend → Vercel
```bash
cd frontend
npx vercel --prod
# Set in Vercel dashboard:
# NEXT_PUBLIC_BACKEND_URL = https://isl-translator-api.onrender.com
```

---

## BDD Scenarios (Acceptance Criteria)

### Scenario 1: Webcam sign detection
```
Given the user has granted camera permission
When they perform an ISL sign for "namaste" in front of the camera
Then within 2 seconds the word "namaste" appears in the word bubble row
And the confidence indicator shows ≥ 85%
```

### Scenario 2: Sentence formation
```
Given the word buffer contains ["i", "am", "good"]
When 2 seconds pass with no new sign detected
Then a grammatically correct sentence appears in the sentence box
And the word buffer clears
```

### Scenario 3: Video file upload
```
Given the user uploads a valid .mp4 file under 50MB
When they click Translate
Then a progress indicator appears
And within 30 seconds the full sentence translation appears
```

### Scenario 4: Cold start handling
```
Given the Render backend is sleeping
When the frontend makes a request
Then a "Warming up server..." message appears
And the frontend retries automatically every 3 seconds for up to 30 seconds
```

### Scenario 5: Low confidence rejection
```
Given the Transformer predicts a sign with confidence < 85%
When the prediction is returned
Then it is NOT added to the word buffer
And no word appears on screen
```

### Scenario 6: Model loaded once
```
Given the FastAPI server starts up
When load_model() is called via lifespan
Then the Transformer weights are loaded exactly once
And all subsequent /predict calls reuse the same model instance
```

---

## Build Order (Antigravity follows this exactly, one phase at a time)

```
Phase 1: Project scaffold
  → Full folder structure
  → FastAPI /health endpoint
  → Next.js 14 blank page
  → Both run locally

Phase 2: MediaPipe landmark extraction
  → landmark_extractor.py
  → Test on sample video: verify output shape (30, 2172)
  → Unit test: input video → output shape assertion

Phase 3: Dataset preprocessing
  → preprocess.py on INCLUDE dataset
  → Verify .npy files saved, shapes correct, no NaN

Phase 4: Transformer training
  → train.py with ISLTransformer architecture
  → Augmentation: time shift, gaussian noise, horizontal flip
  → Train 60 epochs, save when val_acc > 92%

Phase 5: Sign recognizer API
  → sign_recognizer.py: load_model() + predict_sign()
  → Wire to /predict/frame-sequence
  → Test with curl / Postman

Phase 6: Sentence builder
  → sentence_builder.py with Gemini 2.5 Flash
  → Wire to /sentence endpoint
  → Test: ["i", "am", "good"] → verify natural sentence

Phase 7: Frontend webcam
  → WebcamCapture component
  → Connect to /predict/frame-sequence
  → Word bubbles appear live

Phase 8: Frontend video upload
  → VideoUpload component
  → Connect to /predict/video
  → Full translation displayed

Phase 9: Deploy
  → Backend to Render (with weights on persistent disk)
  → Frontend to Vercel
  → End-to-end test on production URLs
```

---

## .gitignore
```
data/
backend/weights/
backend/.env
frontend/.env.local
__pycache__/
*.pyc
.DS_Store
node_modules/
.next/
*.pt
*.pth
label_map.json
```

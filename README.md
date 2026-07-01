# HyperTranslator

Real-time Indian Sign Language (ISL) to English translator using MediaPipe 
Holistic + Transformer Encoder (PyTorch) + Gemini 2.5 Flash.

## Architecture
Webcam → MediaPipe Holistic → Landmark Array (30, 2172)
→ Transformer Encoder (263 classes) → Gemini 3.5 Flash → English Sentence

## Tech Stack
- **Sign Recognition:** PyTorch Transformer Encoder, MediaPipe Holistic
- **Sentence Generation:** Gemini 2.5 Flash
- **Backend:** FastAPI (Python 3.11)
- **Frontend:** Next.js 14 (App Router)
- **Dataset:** INCLUDE ISL — IIT Bombay, 263 classes, ~4,287 clips

## Build Status
| Phase | Description | Status |
|---|---|---|
| 1 | Project Scaffold + FastAPI | ✅ Done |
| 2 | MediaPipe Landmark Extraction | ✅ Done |
| 3 | Dataset Preprocessing | 🔄 In Progress |
| 4 | Transformer Training | ⬜ Pending |
| 5 | Sign Recognizer API | ⬜ Pending |
| 6 | Gemini Sentence Builder | ⬜ Pending |
| 7-9 | Frontend + Deployment | ⬜ Pending |

## Landmark Extraction
- Processes 30 frames per sign (even sampling + zero-padding)
- 2172 features per frame: pose (33) + left hand (21) + right hand (21) + face (468) landmarks
- Tested: output shape `(30, 2172)`, no NaN values

## Target Performance
- ≥92% validation accuracy on 263 ISL classes
- ≤100ms inference on CPU

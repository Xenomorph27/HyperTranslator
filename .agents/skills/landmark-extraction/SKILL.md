---
name: landmark-extraction
description: |
  Extracts MediaPipe Holistic landmarks from ISL video clips and saves them as
  numpy arrays for LSTM training. Use this skill when preprocessing video files
  from the INCLUDE dataset, extracting hand/pose/face landmarks from .mp4 or
  .webm files, or converting raw video into (30, 2172) landmark sequences.
  Do NOT use for audio files, image files, or anything that is not a video.
version: 1.0.0
license: MIT
allowed-tools: Read Bash Write
metadata:
  author: isl-translator-team
  tier: read-only
---

# Landmark Extraction Skill

## When to use
- User asks to preprocess the INCLUDE dataset
- User asks to extract landmarks from a video file
- Any step that converts `.mp4`/`.webm` → `.npy` array
- Running `training/preprocess.py`

## When NOT to use
- Input is not a video file (reject audio, images, text)
- User wants to run inference — use `sign-recognizer` skill instead
- User wants to train the model — that is a separate step after this one

## Workflow

1. **Validate input** — check file exists, extension is `.mp4` or `.webm`, size < 500MB
2. **Load video** with OpenCV (`cv2.VideoCapture`)
3. **Sample exactly 30 frames** evenly spaced across the video duration
   - If video has fewer than 30 frames: pad with zero arrays at the end
   - If video has more than 30 frames: sample evenly, do not just take first 30
4. **Run MediaPipe Holistic** on each frame
   - Extract: pose (33 landmarks × 4), left hand (21 × 4), right hand (21 × 4), face (468 × 4)
   - Total per frame: (33 + 21 + 21 + 468) × 4 = 2172 floats
   - If no hand detected in a frame: fill that region with zeros (do NOT skip the frame)
5. **Stack into numpy array** of shape `(30, 2172)`
6. **Validate output** — assert shape is exactly `(30, 2172)`, assert no NaN values
7. **Save as `.npy`** to `data/landmarks/<original_filename>.npy`

## Key implementation detail
```python
import mediapipe as mp
import cv2
import numpy as np

# IMPORTANT: use this exact version
# mediapipe==0.10.9
# Newer versions break the Holistic API

mp_holistic = mp.solutions.holistic

def extract_landmarks_from_frame(frame, holistic):
    result = holistic.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    
    def get_landmarks(landmark_list, n):
        if landmark_list:
            return np.array([[l.x, l.y, l.z, l.visibility if hasattr(l, 'visibility') else 0]
                             for l in landmark_list.landmark]).flatten()
        return np.zeros(n * 4)
    
    pose  = get_landmarks(result.pose_landmarks, 33)
    lhand = get_landmarks(result.left_hand_landmarks, 21)
    rhand = get_landmarks(result.right_hand_landmarks, 21)
    face  = get_landmarks(result.face_landmarks, 468)
    
    return np.concatenate([pose, lhand, rhand, face])  # shape: (2172,)
```

## Examples
- Input: `data/include_raw/hello_001.mp4` → Output: `data/landmarks/hello_001.npy` shape `(30, 2172)`
- Input: `data/include_raw/namaste_003.mp4` → Output: `data/landmarks/namaste_003.npy` shape `(30, 2172)`

## Output format
- File: `data/landmarks/<filename>.npy`
- Array shape: `(30, 2172)` float32
- No NaN values — replace any NaN with 0.0

## Anti-patterns to avoid
- Don't take just the first 30 frames — sample evenly across the full video
- Don't skip frames where hands aren't visible — fill with zeros instead
- Don't use mediapipe version > 0.10.9 — the Holistic API changed
- Don't store raw BGR pixel data — only store landmark floats
- Don't run this inside FastAPI — preprocessing is offline only

## Eval cases
See `evals/eval_cases.json` → cases `landmark_extraction_001`, `landmark_extraction_002`, `landmark_extraction_003`

## Graduation tier
**Read-Only** — this skill only reads video files and writes `.npy` files to `data/`. It does not touch the backend, API, or any production system.

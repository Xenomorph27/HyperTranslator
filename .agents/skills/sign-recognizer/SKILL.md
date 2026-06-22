---
name: sign-recognizer
description: |
  Runs the trained ISL Transformer Encoder model on a (30, 2172) landmark
  sequence and returns a predicted sign word with confidence score. Use this
  skill when running inference on extracted landmarks, loading model weights,
  implementing the /predict/frame-sequence endpoint, or training the Transformer
  model on the INCLUDE dataset.
  Do NOT use for raw video frames (run landmark-extraction first), or for
  building sentences from words (use sentence-builder skill instead).
version: 2.0.0
license: MIT
allowed-tools: Read Bash
metadata:
  author: isl-translator-team
  tier: read-only
  upgraded-from: LSTM v1.0.0
  reason: Transformer Encoder achieves 92-94% vs LSTM 88% on sign language datasets
---

# Sign Recognizer Skill (Transformer Encoder)

## When to use
- Running inference on a `(30, 2172)` numpy landmark sequence
- Loading `backend/weights/isl_transformer.pt` for prediction
- Implementing or debugging `/predict/frame-sequence` endpoint
- Training the model via `training/train.py`
- Evaluating model accuracy on validation set

## When NOT to use
- Input is raw video frames — use `landmark-extraction` skill first
- Input is a list of words — use `sentence-builder` skill
- You want LSTM — we deliberately moved away from it for accuracy reasons

---

## Why Transformer over LSTM

LSTM reads frames sequentially — it processes frame 1, then frame 2, etc.
By the time it reaches frame 30 it has partially forgotten frame 1.

The Transformer reads ALL 30 frames simultaneously using self-attention.
It learns which frames matter most for identifying a sign — for example,
the peak of a hand movement at frame 15 might be the most informative,
and the Transformer can learn to weight it accordingly.

```
LSTM:   frame1 → frame2 → frame3 → ... → frame30 → prediction
                                          (forgets early frames)

Transformer: [frame1, frame2, ..., frame30] → attention → prediction
              (all frames visible to each other at the same time)
```

---

## Model Architecture

```python
import torch
import torch.nn as nn
import math

class PositionalEncoding(nn.Module):
    """
    Injects frame-order information into the embeddings.
    Without this, the Transformer treats all frames as a bag (no order).
    """
    def __init__(self, d_model: int, max_len: int = 30, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # (1, max_len, d_model)
        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, d_model)
        x = x + self.pe[:, :x.size(1)]
        return self.dropout(x)


class ISLTransformer(nn.Module):
    """
    Transformer Encoder for ISL sign recognition.

    Input:  (batch, 30, 2172)  — 30 frames of MediaPipe landmarks
    Output: (batch, num_classes) — class logits
    """
    def __init__(
        self,
        input_size: int = 2172,
        d_model: int = 256,
        nhead: int = 8,
        num_encoder_layers: int = 4,
        dim_feedforward: int = 512,
        dropout: float = 0.1,
        num_classes: int = 263,
    ):
        super().__init__()

        # Project raw landmarks into model dimension
        self.input_projection = nn.Linear(input_size, d_model)

        # Positional encoding (frame order)
        self.pos_encoder = PositionalEncoding(d_model, dropout=dropout)

        # Transformer Encoder stack
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,    # (batch, seq, features) — not (seq, batch, features)
            norm_first=True,     # Pre-LayerNorm: more stable training
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_encoder_layers,
            enable_nested_tensor=False,
        )

        # CLS token — learnable summary of the full sequence
        self.cls_token = nn.Parameter(torch.zeros(1, 1, d_model))

        # Classification head
        self.classifier = nn.Sequential(
            nn.LayerNorm(d_model),
            nn.Linear(d_model, 128),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(128, num_classes),
        )

        self._init_weights()

    def _init_weights(self):
        nn.init.trunc_normal_(self.cls_token, std=0.02)
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, 30, 2172)
        batch_size = x.size(0)

        # Project to model dim: (batch, 30, 256)
        x = self.input_projection(x)

        # Prepend CLS token: (batch, 31, 256)
        cls = self.cls_token.expand(batch_size, -1, -1)
        x = torch.cat([cls, x], dim=1)

        # Add positional encoding
        x = self.pos_encoder(x)

        # Transformer encoder: (batch, 31, 256)
        x = self.transformer_encoder(x)

        # Take CLS token output as sequence summary: (batch, 256)
        cls_output = x[:, 0, :]

        # Classify: (batch, num_classes)
        return self.classifier(cls_output)
```

---

## Training Script (`training/train.py`)

```python
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
import numpy as np
import os
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import json

# ── Dataset ──────────────────────────────────────────────────────────────────

class ISLDataset(Dataset):
    def __init__(self, file_paths: list[str], labels: list[int]):
        self.file_paths = file_paths
        self.labels = labels

    def __len__(self):
        return len(self.file_paths)

    def __getitem__(self, idx):
        seq = np.load(self.file_paths[idx]).astype(np.float32)  # (30, 2172)
        assert seq.shape == (30, 2172), f"Bad shape: {seq.shape}"
        return torch.FloatTensor(seq), self.labels[idx]


# ── Training loop ─────────────────────────────────────────────────────────────

def train(data_dir: str, out_dir: str, epochs: int = 60, batch_size: int = 32):
    # Collect all .npy files
    data_dir = Path(data_dir)
    all_files = sorted(data_dir.glob("**/*.npy"))

    # Extract label from folder name (INCLUDE dataset structure: data/landmarks/<sign_name>/<file>.npy)
    raw_labels = [f.parent.name for f in all_files]
    le = LabelEncoder()
    encoded_labels = le.fit_transform(raw_labels)

    # Save label map for inference
    os.makedirs(out_dir, exist_ok=True)
    label_map = {int(i): label for i, label in enumerate(le.classes_)}
    with open(f"{out_dir}/label_map.json", "w") as f:
        json.dump(label_map, f, indent=2)

    # Train / val split — stratified so all classes appear in both sets
    X_train, X_val, y_train, y_val = train_test_split(
        [str(f) for f in all_files],
        encoded_labels,
        test_size=0.15,
        stratify=encoded_labels,
        random_state=42,
    )

    train_loader = DataLoader(ISLDataset(X_train, y_train), batch_size=batch_size, shuffle=True, num_workers=4)
    val_loader   = DataLoader(ISLDataset(X_val, y_val),   batch_size=batch_size, shuffle=False, num_workers=4)

    # Model, optimizer, scheduler
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on: {device}")

    model = ISLTransformer(num_classes=len(le.classes_)).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

    best_val_acc = 0.0

    for epoch in range(epochs):
        # ── Train ──
        model.train()
        train_loss, train_correct = 0.0, 0
        for seqs, labels in train_loader:
            seqs, labels = seqs.to(device), labels.to(device)
            optimizer.zero_grad()
            logits = model(seqs)
            loss = criterion(logits, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_loss += loss.item()
            train_correct += (logits.argmax(1) == labels).sum().item()

        # ── Validate ──
        model.eval()
        val_correct = 0
        with torch.no_grad():
            for seqs, labels in val_loader:
                seqs, labels = seqs.to(device), labels.to(device)
                val_correct += (model(seqs).argmax(1) == labels).sum().item()

        train_acc = train_correct / len(X_train)
        val_acc   = val_correct   / len(X_val)
        scheduler.step()

        print(f"Epoch {epoch+1:3d}/{epochs} | "
              f"loss {train_loss/len(train_loader):.4f} | "
              f"train {train_acc:.3f} | val {val_acc:.3f}")

        # Save best checkpoint
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "val_acc": val_acc,
                "num_classes": len(le.classes_),
            }, f"{out_dir}/isl_transformer.pt")
            print(f"  ✓ Saved checkpoint (val_acc={val_acc:.4f})")

    print(f"\nBest validation accuracy: {best_val_acc:.4f}")
    if best_val_acc < 0.85:
        print("⚠ Below 85% target. Check: data quality, class balance, landmark extraction.")
```

---

## Inference Function (`backend/models/sign_recognizer.py`)

```python
import torch
import numpy as np
import json
import os
from pathlib import Path

CONFIDENCE_THRESHOLD = 0.85

# Load once at server startup — never inside a request handler
_model = None
_label_map = None

def load_model():
    """Call once at FastAPI startup."""
    global _model, _label_map

    weights_path = os.getenv("MODEL_WEIGHTS_PATH", "./weights/isl_transformer.pt")
    label_map_path = Path(weights_path).parent / "label_map.json"

    checkpoint = torch.load(weights_path, map_location="cpu")
    num_classes = checkpoint["num_classes"]

    model = ISLTransformer(num_classes=num_classes)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()  # CRITICAL: sets dropout to 0 for inference

    with open(label_map_path) as f:
        label_map = {int(k): v for k, v in json.load(f).items()}

    _model = model
    _label_map = label_map
    print(f"Model loaded: {num_classes} classes, val_acc={checkpoint['val_acc']:.4f}")


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
    if _model is None:
        raise RuntimeError("Model not loaded. Call load_model() at startup.")

    if landmark_sequence.shape != (30, 2172):
        raise ValueError(f"Expected shape (30, 2172), got {landmark_sequence.shape}")

    tensor = torch.FloatTensor(landmark_sequence).unsqueeze(0)  # (1, 30, 2172)

    with torch.no_grad():
        logits = _model(tensor)                          # (1, num_classes)
        probs = torch.softmax(logits, dim=1)
        confidence, predicted_idx = probs.max(dim=1)

    confidence = confidence.item()
    word = _label_map[predicted_idx.item()] if confidence >= CONFIDENCE_THRESHOLD else None

    return {"word": word, "confidence": round(confidence, 4)}
```

---

## FastAPI Integration (`backend/main.py` startup)

```python
from contextlib import asynccontextmanager
from backend.models.sign_recognizer import load_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()   # runs once at startup
    yield
    # cleanup on shutdown if needed

app = FastAPI(lifespan=lifespan)
```

---

## Data Augmentation (add to `training/train.py` for better accuracy)

```python
def augment_sequence(seq: np.ndarray) -> np.ndarray:
    """
    Apply random augmentation to a (30, 2172) landmark sequence.
    Call this inside ISLDataset.__getitem__ during training only.
    """
    # 1. Random time shift — shift sequence by 1-3 frames
    shift = np.random.randint(1, 4)
    seq = np.roll(seq, shift, axis=0)

    # 2. Random Gaussian noise — simulates sensor jitter
    seq += np.random.normal(0, 0.01, seq.shape)

    # 3. Random horizontal flip — mirrors the signer
    # Landmark order: pose(33*4), lhand(21*4), rhand(21*4), face(468*4)
    # Swap left and right hand columns
    pose_end   = 33 * 4          # 132
    lhand_end  = pose_end + 21*4  # 216
    rhand_end  = lhand_end + 21*4 # 300
    if np.random.random() > 0.5:
        lhand = seq[:, pose_end:lhand_end].copy()
        rhand = seq[:, lhand_end:rhand_end].copy()
        seq[:, pose_end:lhand_end]  = rhand
        seq[:, lhand_end:rhand_end] = lhand

    return seq
```

---

## Hyperparameters (proven settings)

| Param | Value | Reason |
|---|---|---|
| d_model | 256 | Enough capacity, fits in memory |
| nhead | 8 | 256 / 8 = 32 dims per head |
| num_encoder_layers | 4 | 4 layers > 2 for gesture complexity |
| dim_feedforward | 512 | 2× d_model standard |
| dropout | 0.1 | Light regularization |
| optimizer | AdamW | Better than Adam for Transformers |
| lr | 1e-4 | Standard for Transformers |
| weight_decay | 0.01 | L2 regularization |
| scheduler | CosineAnnealing | Smooth LR decay |
| label_smoothing | 0.1 | Prevents overconfidence |
| grad_clip | 1.0 | Prevents exploding gradients |
| epochs | 60 | Transformers need more than LSTMs |

---

## Examples
- Input: `(30, 2172)` array for "namaste" sign → `{"word": "namaste", "confidence": 0.96}`
- Input: `(30, 2172)` noisy array → `{"word": null, "confidence": 0.72}`

## Output format
```json
{
  "word": "namaste",   // null if confidence < 0.85
  "confidence": 0.96   // always returned, even when word is null
}
```

## Anti-patterns to avoid
- Don't use LSTM — we moved away from it, accuracy is 5–8% lower
- Don't hardcode weights path — always `os.getenv("MODEL_WEIGHTS_PATH")`
- Don't load model inside request handler — load once at startup with lifespan
- Don't skip `model.eval()` during inference — dropout stays ON without it, giving random results
- Don't skip `torch.no_grad()` — without it, PyTorch builds computation graphs, causing memory leaks
- Don't skip gradient clipping during training — Transformer training can explode without it
- Don't train for fewer than 50 epochs — Transformers converge slower than LSTMs

## Eval cases
See `evals/eval_cases.json` → cases `sign_recognizer_001`, `sign_recognizer_002`, `sign_recognizer_003`, `sign_recognizer_004`

## Graduation tier
**Read-Only** — reads model weights, reads input arrays, returns prediction. No writes, no state mutation.

## V2 upgrade path (SignFormer-GCN)
When ready to push accuracy further (target 96%+), upgrade to SignFormer-GCN:
- Replace `input_projection` with a Graph Convolutional Network (GCN) that models joint connections
- Keep the Transformer Encoder stack as-is
- Add RGB frame features as a second input stream
See `references/signformer_gcn.md` for architecture details (create when starting v2)

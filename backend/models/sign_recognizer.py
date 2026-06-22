import numpy as np

def load_model():
    """Call once at FastAPI startup."""
    pass

def predict_sign(landmark_sequence: np.ndarray) -> dict:
    """
    Predict ISL sign from landmark sequence.
    """
    return {"word": None, "confidence": 0.0}

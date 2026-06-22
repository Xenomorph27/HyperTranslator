# Testing Patterns

**Analysis Date:** 2026-06-22

## Test Framework

**Runner:**
- pytest (planned, not yet configured)
- Config: `backend/tests/` directory (to be created)

**Assertion Library:**
- pytest built-in assertions
- numpy testing utilities for array shape/value assertions

**Run Commands:**
```bash
cd backend && pytest                  # Run all tests
cd backend && pytest -v               # Verbose output
cd backend && pytest --cov=.          # Coverage report
```

## Test File Organization

**Location:**
- Separate test directory: `backend/tests/`
- Every backend route must have a corresponding test file

**Naming:**
- `test_<module>.py` — e.g., `test_sign_recognizer.py`, `test_sentence_builder.py`, `test_main.py`

**Structure:**
```text
backend/
├── tests/
│   ├── __init__.py
│   ├── test_main.py              # API route tests
│   ├── test_sign_recognizer.py   # Model inference tests
│   ├── test_sentence_builder.py  # Gemini integration tests
│   └── test_landmark_extractor.py # Landmark extraction tests
```

## Test Structure

**Suite Organization:**
```python
import pytest
import numpy as np

class TestSignRecognizer:
    """Tests for sign_recognizer.predict_sign()."""

    def test_valid_input_returns_prediction(self, loaded_model):
        """Given valid (30, 2172) input, returns word and confidence."""
        seq = np.random.randn(30, 2172).astype(np.float32)
        result = predict_sign(seq)
        assert "word" in result
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0

    def test_wrong_shape_raises_value_error(self):
        """Given wrong input shape, raises ValueError with shape info."""
        seq = np.random.randn(25, 2172).astype(np.float32)
        with pytest.raises(ValueError, match="Expected shape"):
            predict_sign(seq)

    def test_low_confidence_returns_null_word(self, noisy_input):
        """Given noisy input, word is None but confidence is returned."""
        result = predict_sign(noisy_input)
        assert result["word"] is None
        assert result["confidence"] < 0.85
```

**Patterns:**
- Use class-based test grouping for related tests
- Descriptive test names: `test_<what>_<condition>_<expected>`
- Setup via fixtures or class setup methods
- Teardown via pytest fixtures with yield

## Mocking

**Framework:** pytest + `unittest.mock`

**Patterns:**
```python
from unittest.mock import patch, MagicMock

class TestSentenceBuilder:
    @patch("backend.models.sentence_builder.genai.GenerativeModel")
    def test_gemini_failure_uses_fallback(self, mock_model):
        """When Gemini API fails, fallback joins words."""
        mock_model.return_value.generate_content.side_effect = Exception("API timeout")
        result = build_sentence(["name", "what", "you"])
        assert result == "Name what you."

    @patch("backend.models.sentence_builder.genai.GenerativeModel")
    def test_gemini_success_returns_sentence(self, mock_model):
        """When Gemini succeeds, returns grammatical sentence."""
        mock_response = MagicMock()
        mock_response.text = "What is your name?"
        mock_model.return_value.generate_content.return_value = mock_response
        result = build_sentence(["name", "what", "you"])
        assert result == "What is your name?"
```

**What to Mock:**
- Gemini API calls (external service, costs money)
- File system operations for model weight loading
- MediaPipe processing (requires OpenCV + camera drivers)

**What NOT to Mock:**
- Numpy array operations (fast, deterministic)
- PyTorch tensor operations (test actual model behavior)
- Input validation logic (test real validation)

## Fixtures and Factories

**Test Data:**
```python
import pytest
import numpy as np

@pytest.fixture
def valid_landmark_sequence():
    """Create a valid (30, 2172) random landmark sequence."""
    return np.random.randn(30, 2172).astype(np.float32)

@pytest.fixture
def sample_word_list():
    """Common word list for sentence builder tests."""
    return ["i", "good", "morning"]

@pytest.fixture
def loaded_model(tmp_path):
    """Load model with test weights for inference tests."""
    # Create minimal test weights
    ...
```

**Location:**
- Fixtures in `backend/tests/conftest.py`
- Test data files in `backend/tests/fixtures/` (if needed)

## Coverage

**Requirements:** Not yet enforced — recommend ≥80% for backend routes
**View Coverage:**
```bash
cd backend && pytest --cov=. --cov-report=html
# Open htmlcov/index.html
```

## Test Types

**Unit Tests:**
- Scope: Individual functions (predict_sign, build_sentence, extract_landmarks)
- Approach: Mock external dependencies, test logic in isolation
- Location: `backend/tests/test_<module>.py`

**Integration Tests:**
- Scope: FastAPI endpoint round-trips
- Approach: Use FastAPI TestClient, test full request → response cycle
- Location: `backend/tests/test_main.py`

**E2E Tests:**
- Framework: Not yet configured
- Plan: Playwright or Cypress for frontend (Phase 9)

## Eval-Driven Development (EDD)

**The project uses EDD via `evals/eval_cases.json`:**

Each eval case defines:
- `case_id`: Unique identifier (e.g., `landmark_extraction_001`)
- `description`: What the case tests
- `input`: Test input data
- `expected_skill`: Which skill should handle this
- `expected_output_format`: Expected output structure
- `rubric`: Pass/fail criteria

**Current eval cases (13 total):**
- `landmark_extraction_001` through `003` — Video preprocessing tests
- `sign_recognizer_001` through `005` — Transformer inference tests
- `sentence_builder_001` through `004` — Gemini sentence building tests
- `code_review_001` through `003` — PR review tests

**Workflow:** Read eval cases before coding → write failing tests → implement → verify pass

## Common Patterns

**Async Testing (FastAPI):**
```python
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

**Error Testing:**
```python
def test_empty_word_list_raises_error():
    with pytest.raises(ValueError, match="Word list is empty"):
        build_sentence([])

def test_wrong_shape_returns_422():
    response = client.post("/predict/frame-sequence", json={
        "frames": [[0.0] * 2172] * 25,  # Wrong: 25 frames instead of 30
        "session_id": "test"
    })
    assert response.status_code == 422
```

**Shape Assertion:**
```python
def test_landmark_output_shape():
    """Output must be exactly (30, 2172) — the full pipeline depends on this."""
    result = extract_landmarks("test_video.mp4")
    assert result.shape == (30, 2172)
    assert not np.isnan(result).any()
```

---

*Testing analysis: 2026-06-22*

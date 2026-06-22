---
name: sentence-builder
description: |
  Converts a list of raw ISL sign words into a grammatically correct English
  sentence using the Gemini API. Use this skill when the word buffer is flushed,
  when implementing the /sentence endpoint, or when testing word-to-sentence
  conversion. Do NOT use for empty word lists or when input is raw video/landmarks.
version: 1.0.0
license: MIT
allowed-tools: Read Bash
metadata:
  author: isl-translator-team
  tier: draft-only
---

# Sentence Builder Skill

## When to use
- Word buffer has been flushed (2 seconds of silence detected)
- Implementing or debugging the `/sentence` FastAPI endpoint
- Testing Gemini API integration
- Any step that converts `["i", "good", "morning"]` → `"Good morning, I am well."`

## When NOT to use
- Word list is empty — validate first, do NOT call Gemini API
- Input is landmarks or raw video — wrong skill, use `sign-recognizer` first
- You want to classify a sign — that is `sign-recognizer` skill

## Workflow

1. **Validate input** — word list must be non-empty, all items must be strings
2. **Build prompt** — use the exact prompt template below (do not improvise)
3. **Call Gemini API** — use `gemini-1.5-flash`, max_tokens=100
4. **Parse response** — strip whitespace, verify it is a non-empty string
5. **Fallback** — if Gemini call fails, join words with spaces as plain fallback
6. **Return sentence**

## Prompt template (use exactly this)
```python
def build_prompt(words: list[str]) -> str:
    return f"""You are a helpful assistant converting Indian Sign Language word tokens to natural English.

The signer produced these words in order: {', '.join(words)}

Convert this into one natural, grammatically correct English sentence.
Rules:
- Return ONLY the sentence, no explanation, no quotes
- Keep the original meaning of all words
- Fix grammar naturally (ISL omits articles and verb-to-be)
- Maximum one sentence"""
```

## Implementation
```python
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def build_sentence(words: list[str]) -> str:
    """
    Convert ISL sign word tokens to a grammatical English sentence.
    
    Args:
        words: list of sign words e.g. ["i", "good", "morning"]
    
    Returns:
        Grammatical English sentence e.g. "Good morning, I am doing well."
    
    Raises:
        ValueError: if words list is empty
    """
    if not words:
        raise ValueError("Word list is empty. Cannot build sentence.")
    
    prompt = build_prompt(words)
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(max_output_tokens=100)
        )
        sentence = response.text.strip()
        if not sentence:
            raise ValueError("Gemini returned empty response")
        return sentence
    except Exception as e:
        # Graceful fallback — never let this crash the app
        fallback = " ".join(words).capitalize() + "."
        print(f"[sentence-builder] Gemini failed: {e}. Using fallback: {fallback}")
        return fallback
```

## Word buffer logic (where this skill gets triggered)
```python
import time

class WordBuffer:
    SILENCE_THRESHOLD_SECONDS = 2.0
    
    def __init__(self):
        self.words = []
        self.last_sign_time = None
    
    def add_word(self, word: str):
        self.words.append(word)
        self.last_sign_time = time.time()
    
    def should_flush(self) -> bool:
        if not self.words or self.last_sign_time is None:
            return False
        return (time.time() - self.last_sign_time) > self.SILENCE_THRESHOLD_SECONDS
    
    def flush(self) -> list[str]:
        words = self.words.copy()
        self.words.clear()
        self.last_sign_time = None
        return words
```

## Examples
- Input: `["i", "good", "morning"]` → Output: `"Good morning, I am doing well."`
- Input: `["hello"]` → Output: `"Hello there!"`
- Input: `["name", "what", "you"]` → Output: `"What is your name?"`
- Input: `[]` → raises `ValueError` (do NOT call Gemini)

## Output format
```json
{
  "sentence": "Good morning, I am doing well.",
  "words_used": ["i", "good", "morning"],
  "used_fallback": false
}
```

## Anti-patterns to avoid
- Don't call Gemini with an empty word list — validate first
- Don't hardcode `GEMINI_API_KEY` — always from env variable
- Don't let Gemini failures crash the endpoint — always have a fallback
- Don't use `gemini-1.0-pro` — use `gemini-1.5-flash` for speed
- Don't return Gemini's full response object — strip to text only

## Eval cases
See `evals/eval_cases.json` → cases `sentence_builder_001`, `sentence_builder_002`, `sentence_builder_003`

## Graduation tier
**Draft-Only** — calls external API (Gemini), produces content shown to user. Requires human to verify output quality before promoting to Action-Allowed.

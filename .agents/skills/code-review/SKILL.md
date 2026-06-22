---
name: code-review
description: |
  Reviews GitHub PRs for the ISL translator project checking for security
  vulnerabilities, hardcoded secrets, ML-specific bugs, and code quality.
  Use this skill when a PR is opened or updated, when asked to review a diff,
  or when running automated review via GitHub Actions.
  Do NOT use for markdown-only PRs or documentation-only changes.
version: 1.0.0
license: MIT
allowed-tools: Read Bash
metadata:
  author: isl-translator-team
  tier: draft-only
---

# Code Review Skill

## When to use
- A PR is opened or updated with `.py`, `.ts`, `.tsx`, or `.json` changes
- User says "review this PR" or "check this diff"
- Running automated review in CI via GitHub Actions
- Checking for hardcoded secrets before merge

## When NOT to use
- PR only contains `.md`, `.txt`, or `specs/` changes — skip, return "no code changes"
- User wants to run training — wrong skill
- User wants to extract landmarks — wrong skill

## Workflow

1. **Fetch PR diff** using `gh pr view <PR_NUMBER> --json files,additions,deletions`
2. **Check file types** — if only docs/markdown, return early with skip message
3. **Run secret scan** — check for hardcoded API keys, passwords, tokens
4. **Run ML-specific checks** — see checklist below
5. **Run general code quality checks** — see checklist below
6. **Post review comment** via `gh pr review`

## Review checklist

### 🔴 Critical (block merge immediately)
- Hardcoded API keys, tokens, passwords (`GEMINI_API_KEY = "..."`, `password = "abc"`)
- Model weights committed to git (`*.pt`, `*.pth`, `*.pkl` files)
- Raw dataset committed to git (`data/` folder)
- SQL injection or command injection in any endpoint
- CORS set to `allow_origins=["*"]` in production config
- Missing input validation on file upload endpoints

### 🟡 Warnings (flag, don't block)
- Missing type hints on Python functions
- `any` type used in TypeScript
- No try/except around Gemini API calls
- MediaPipe version not pinned to `0.10.9`
- Model loaded inside request handler instead of at startup
- `print()` used instead of `logging` in backend code

### 🔵 Best practices (suggest, don't block)
- Functions longer than 50 lines — suggest splitting
- Missing docstring on public functions
- Test file missing for new module
- No error message returned with HTTP error codes

### 🤖 ML-specific checks
- Landmark shape assertion missing before inference
- Confidence threshold not applied before adding to word buffer
- Training code mixed into inference code (they must stay separate)
- `torch.no_grad()` missing during inference (causes memory leak)
- Batch normalization/dropout not set to `eval()` mode during inference

## Review prompt template
```
Act as a Senior ML Engineer and Security Researcher reviewing a PR for an
ISL (Indian Sign Language) to text translation system.

Fetch the PR:
`gh pr view {PR_NUMBER}`

Analyze the diff, then review using these criteria:

1. CRITICAL: hardcoded secrets, missing input validation, model/data in git,
   unsafe CORS, injection vulnerabilities
2. ML-SPECIFIC: landmark shape checks, confidence thresholds, inference mode,
   no_grad context, training/inference separation
3. LOGIC: off-by-one in frame sampling, word buffer not clearing, 
   incorrect landmark concatenation order (pose+lhand+rhand+face)
4. CODE QUALITY: type hints, docstrings, error handling, logging vs print
5. TESTS: is there a test for every new function?

Output format:
- Description: what does this PR do?

ISSUES:
- Critical: (stop-ship)
- Warnings: (fix before merge)  
- ML Issues: (ML-specific problems)
- Best Practices: (suggestions)
- Quick Win: one sentence, biggest improvement

If no issues: return "Description: ... \n\nLGTM ✅"
```

## Examples
- Input: PR #12 adds hardcoded `GEMINI_API_KEY` → Output: CRITICAL flag, block merge
- Input: PR #15 adds new FastAPI route without tests → Output: Warning, suggest adding test
- Input: PR #18 updates only `README.md` → Output: "No code changes detected, skipping review"

## Output format
```
Description: [what the PR does]

ISSUES:
- Critical: [list or "None"]
- Warnings: [list or "None"]
- ML Issues: [list or "None"]  
- Best Practices: [list or "None"]
- Quick Win: [one sentence]
```

## Anti-patterns to avoid
- Don't trigger on docs-only PRs — waste of tokens
- Don't approve a PR with any Critical issue — always block
- Don't repeat the entire diff in your response — summarize only
- Don't flag style issues as Critical — keep severity accurate

## Eval cases
See `evals/eval_cases.json` → cases `code_review_001`, `code_review_002`

## Graduation tier
**Draft-Only** — posts review comments to GitHub. Cannot merge or approve PRs automatically. Human must take final merge action.

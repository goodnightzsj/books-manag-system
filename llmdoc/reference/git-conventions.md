# Git Conventions

This document summarizes the repository's currently observable git habits.

## 1. Core Summary

The project is still early-stage and primarily uses a simple `main`-branch workflow. Commit messages observed in history are Chinese and descriptive. A root `.gitignore` now exists.

## 2. Source of Truth

- Primary branch: `main`
- Recent commits observed in local history include `1b6b1cd` and `1690701`
- Ignore rules: `/.gitignore:1-24`

## 3. Observed Patterns

| Aspect | Current State |
|---|---|
| Branch strategy | Single `main` branch in current local work |
| Commit language | Chinese |
| Commit style | Free-form descriptive |
| `.gitignore` | Present; excludes env files, caches, uploads, books, editor files |
| Docs workflow | `llmdoc/` is maintained alongside architecture-impacting code changes |

## 4. Current Ignore Coverage

`/.gitignore:1-24` currently excludes:
- Python caches and virtualenvs
- `.env` and `.env.*`
- `backend/uploads/` and `backend/books/`
- Logs, `.DS_Store`, `.idea/`, `.vscode/`

## 5. Notes

- No strict conventional-commit format is enforced by the repository itself.
- No CI-specific branch strategy is documented in-repo.
- The repository contains active architecture documentation under `llmdoc/`, so behavior-changing backend work should keep docs in sync.

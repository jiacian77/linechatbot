# AGENTS.md

## Project overview

This repository contains a Python Flask webhook for a LINE Messaging API bot. It replies to text and image messages using Google Gemini. Keep changes small, readable, and aligned with the existing Python implementation.

## Project structure

- `bot.py` — Flask app, LINE webhook signature validation, message handlers, Gemini calls, and reply delivery.
- `requirements.txt` — Python runtime dependencies.
- `.env.example` — names and placeholders for required configuration; never put real credentials here.
- `.gitignore` — excludes local secrets, virtual environments, and generated files.
- `README.md` — setup, local run, and LINE webhook instructions.
- `outputs/` — reserved for user-facing deliverables; do not place runtime data here.
- `work/` — scratch work; do not commit temporary files unless requested.

## Development

Use Python 3.10 or newer. On Windows PowerShell, create and activate a virtual environment, install dependencies, copy `.env.example` to `.env`, and fill in `CHANNEL_ACCESS_TOKEN`, `CHANNEL_SECRET`, and `GEMINI_API_KEY` before starting the app:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python bot.py
```

The app listens on port 8080 by default. `GET /health` is a simple health check and `POST /callback` is the LINE webhook endpoint. Set `PORT` through the environment when a different port is needed.

Keep credentials in `.env` or the deployment platform's secret store. Never log tokens, API keys, or full message payloads containing private user content. Do not commit `.env`, downloaded credentials, or user data.

When changing webhook behavior, preserve LINE signature validation and return a client error for invalid signatures. Keep handlers resilient to upstream LINE or Gemini failures, and avoid exposing exception details to end users.

## Validation

There is no dedicated test suite in the repository yet. For changes, at minimum compile-check Python files:

```powershell
python -m compileall -q bot.py
```

When credentials and dependencies are available, also start the app and confirm `http://localhost:8080/health` returns `{"status":"ok"}`. Do not send real LINE or Gemini requests during automated checks unless explicitly requested.

If adding tests, use Python's standard `unittest` unless a project dependency already justifies another framework. Keep tests independent of live credentials and external services by mocking those integrations.

## Contribution rules

- Use focused changes and descriptive commit messages.
- Update `README.md` or this file when setup, configuration, or developer workflows change.
- Keep `.env.example` synchronized with configuration names used by the app, using placeholders only.
- Do not commit generated caches, virtual environments, secrets, or unrelated scratch files.
- Review `git diff` and `git status` before committing; run the applicable validation above.
- Preserve existing history and avoid force-pushing shared branches.

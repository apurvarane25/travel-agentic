# travel-agentic

AI travel planner: a FastAPI + LangChain agent (Gemini) in `backend/`, and a Next.js UI in `frontend/`.
Frontend rules are in `frontend/AGENTS.md`.

## Backend
- Python 3.11: `cd backend && source venv/bin/activate`
- Run: `uvicorn main:app --reload` (port 8000).
- Test: `pytest`. Tests use a fake model and fake HTTP, so they need no network or API key. Keep it that way.
- The API contract is `backend/models.py`. After changing it, run `npm run gen:api` in `frontend/` and fix the type errors.
- Tools raise on failure. Never catch errors inside a tool and return them as data; the retry and error middleware in `agent.py` handle failures.

## Always
- Never commit `.env`, `.env.local` or API keys. Keys live only in `backend/.env`.
- Don't add dependencies without asking.
- Keep changes small, and say what changed and why.

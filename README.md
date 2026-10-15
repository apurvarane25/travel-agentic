# Travel Agent

An AI travel assistant: enter a city and dates, and a LangChain tool-calling agent (Gemini) checks the forecast (Open-Meteo) and attractions (Wikipedia), then recommends what to do each day.

**Status:** work in progress.

**Stack:** Python · LangChain · Gemini · FastAPI · Next.js

## Run locally

**Backend**
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your GOOGLE_API_KEY
uvicorn main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open http://localhost:3000. API docs: http://localhost:8000/docs
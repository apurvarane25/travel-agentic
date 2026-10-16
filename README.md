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

## Performance (local baseline)

End-to-end request time measured with `curl` against the backend running locally on a MacBook Air: 3 cities × 3 runs, trip dates within the forecast window (Oct 2026).

| Metric | Time |
|---|---|
| Median | 6.3 s |
| Fastest | 4.4 s |
| Slowest | 23.1 s |

Each request makes 3 sequential Gemini calls (decide to fetch weather → decide to fetch attractions → write the plan) plus up to 3 HTTP calls (geocoding, forecast, Wikipedia), so model latency dominates. Latency varies widely between runs; the 23 s outlier is still being investigated.

**Next:** stream progress so users see activity immediately, and measure the deployed app.
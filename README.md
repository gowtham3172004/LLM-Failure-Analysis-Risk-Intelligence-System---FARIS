# FARIS - LLM Failure Analysis & Risk Intelligence System

FARIS is a full-stack system that analyzes LLM answers, detects failure patterns, computes risk, and returns actionable recommendations.

## What FARIS Does

- Detects six failure types in LLM outputs:
  - hallucination
  - logical_inconsistency
  - missing_assumptions
  - overconfidence
  - scope_violation
  - underspecification
- Produces deterministic risk scoring with domain multipliers.
- Supports optional ground-truth ingestion from URL or PDF before analysis.
- Stores analysis history and exposes case/taxonomy APIs.

## Repository Layout

```text
LLM-Failure-Analysis-Risk-Intelligence-System---FARIS-main/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── services/
│   │   ├── config.py
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── docker-compose.yml
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── .env.example
├── .env.production
└── README.md
```

## LLM Providers

FARIS supports three providers via `LLM_PROVIDER`:

- `gemini`
- `groq`
- `ollama`

Configure at repository root in `.env`.

Important: backend settings are configured to load the root `.env` even if you start Uvicorn from `backend/`.

## Local Setup

### 1. Clone and Enter

```bash
git clone https://github.com/gowtham3172004/LLM-Failure-Analysis-Risk-Intelligence-System---FARIS.git
cd LLM-Failure-Analysis-Risk-Intelligence-System---FARIS-main
```

### 2. Backend Environment

```bash
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 3. Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 4. Environment File

```bash
cp .env.example .env
```

Set provider-specific values in `.env`.

Example (Groq):

```dotenv
LLM_PROVIDER=groq
GROQ_API_KEY=your_key_here
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.1-8b-instant
```

Example (Gemini):

```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-1.5-flash
```

Example (Ollama):

```dotenv
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

## Run the App

Open two terminals from repository root.

### Terminal A - Backend

```bash
source venv/bin/activate
cd backend
python -m uvicorn app.main:app --reload
```

Backend URLs:

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

### Terminal B - Frontend

```bash
cd frontend
npm run dev
```

Frontend URL (Vite):

- App: `http://localhost:8080`

The frontend proxies `/api` and `/health` to backend port `8000`.

## API Endpoints

Main endpoints:

- `POST /api/analyze` (multipart/form-data, supports URL/PDF ingestion)
- `POST /api/analyze/quick` (JSON, no persistence)
- `GET /api/cases`
- `GET /api/cases/{case_id}`
- `DELETE /api/cases/{case_id}`
- `GET /api/cases/statistics/summary`
- `GET /api/taxonomy`
- `GET /health`

## Testing

Run backend tests from repository root:

```bash
source venv/bin/activate
cd backend
pytest
```

## Docker (Backend)

Run from `backend/`:

```bash
docker-compose up -d
```

Stop:

```bash
docker-compose down
```

## Troubleshooting

### Provider mismatch (Gemini used when you set Groq)

- Ensure `.env` is at repository root.
- Ensure `LLM_PROVIDER=groq` in root `.env`.
- Restart backend process after changing `.env`.

### Port already in use

```bash
lsof -ti:8000 | xargs kill -9
lsof -ti:8080 | xargs kill -9
```

### Dependency issues with torch/numpy

Use pinned backend dependencies from `backend/requirements.txt` and reinstall in venv:

```bash
pip install -r backend/requirements.txt
```

## Notes

- Keep real API keys only in `.env` (never commit secrets).
- `.env.example` is the safe template for sharing configuration.

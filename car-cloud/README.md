# Car Cloud

Base full-stack starter for a car information website.

## Structure

- `frontend/` - Next.js app (UI)
- `backend/` - FastAPI app (API)

## 1) Run backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8001
```

Backend URLs:

- `http://127.0.0.1:8001/health`
- `http://127.0.0.1:8001/api/cars`
- `http://127.0.0.1:8001/analyze-vehicle`
- `http://127.0.0.1:8001/vehicle-recalls`
- `http://127.0.0.1:8001/risk-score`
- `http://127.0.0.1:8001/common-failures`
- `http://127.0.0.1:8001/ai-summary`

## 2) Run frontend

```bash
cd frontend
cp .env.local.example .env.local
source "$HOME/.nvm/nvm.sh"
nvm use 20.19.0
npm install
npm run dev
```

Frontend URL:

- `http://localhost:3000`

## Environment

Backend (`backend/.env`):

- `FRONTEND_ORIGIN=http://localhost:3000`
- `OPENROUTER_API_KEY=<optional>`
- `OPENROUTER_BASE_URL=https://openrouter.ai/api/v1`
- `OPENROUTER_MODEL=mistralai/mistral-7b-instruct-v0.1`
- Compatible aliases: `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `LLM_MODEL`

Frontend (`frontend/.env.local`):

- `NEXT_PUBLIC_API_BASE_URL=/car-api`
- `BACKEND_INTERNAL_URL=http://127.0.0.1:8001`

## Notes from project MVP

- Input supports either VIN or Make/Model/Year.
- Backend integrates NHTSA vehicle + recall data.
- Dashboard shows recall alerts, risk score, mileage-based failure insights, and AI summary.

# Odonto Backend (FastAPI)

## Run locally

1) Create venv and install deps:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

2) Create `.env` from `.env.example` and fill Supabase values.

3) Start API:

```bash
uvicorn app.main:app --reload
```

## Auth

This backend validates Supabase `access_token` via `GET /auth/v1/user`.

- `GET /api/v1/auth/me` requires header: `Authorization: Bearer <token>`

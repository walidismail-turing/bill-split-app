# Bill Split App

Two-service setup for deploying to **GCP Cloud Run**:

- **`frontend/`**: Svelte 5 (SvelteKit) UI (Node server via adapter-node)
- **`backend/`**: Django + DRF API (Gunicorn) configured for **Postgres**

## Local development (Docker)

Run everything (Postgres + Django API + Svelte UI):

```bash
docker compose up --build
```

Then open:

- **Frontend**: `http://localhost:5173`
- **Backend health**: `http://localhost:8000/api/healthz/`

## API

### `POST /api/split/`

Splits itemized bills among participants, supports:

- Item assignments (per item: specific participants or “everyone” when empty)
- Tip as **percent** or **fixed amount**
- Optional `total_before_tip` override (useful for tax/fees not itemized)
- Rounding-safe allocation so totals always sum exactly

Example request:

```json
{
  "currency": "USD",
  "participants": [{ "id": "a", "name": "Ava" }, { "id": "b", "name": "Ben" }],
  "items": [
    { "id": "i1", "name": "Pizza", "amount": "10.00", "participants": ["a", "b"] },
    { "id": "i2", "name": "Soda", "amount": "5.00", "participants": ["a"] }
  ],
  "tip_mode": "percent",
  "tip_percent": "18.00",
  "total_before_tip": null
}
```

## Cloud Run notes

### Backend (`backend/`)

- **Required env vars**:
  - `DJANGO_SECRET_KEY`
  - `DJANGO_ALLOWED_HOSTS` (comma-separated; `*` is allowed)
  - `DATABASE_URL` (Postgres)
- **Optional**:
  - `CORS_ALLOWED_ORIGINS` (comma-separated, e.g. your frontend URL)

### Frontend (`frontend/`)

- **Env var**:
  - `PUBLIC_API_BASE` (e.g. `https://<your-backend-service>.run.app`)


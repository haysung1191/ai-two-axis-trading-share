# DDD/Clean Architecture Skeleton

## Directory Layout

```text
app/
  api/
    routes/
  core/
  domains/
    trading/
    backtesting/
    qa/
    settlement/
  infrastructure/
    db/
    cache/
    secrets/
    orchestration/
tests/
  unit/
deploy/
  docker/
    postgres/
      init/
docker-compose.yml
requirements.txt
```

## Run (Docker)

```bash
docker compose up -d
```

## Run (Local)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Endpoints

- `GET /api/v1/status`
- `POST /api/v1/trading/orders`

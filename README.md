# streamer-activity-notify

MVP backend scaffold for streamer activity notification app.

## Stack
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic

## Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic -c alembic.ini upgrade head
uvicorn app.main:app --reload
```

## A-2 API (MVP)
- `POST /users`
- `GET /users`
- `POST /streamers`
- `GET /streamers`
- `POST /watch-targets`
- `GET /watch-targets?user_id={id}`
- `DELETE /watch-targets/{watch_target_id}`

## Initial tables
- users
- streamers
- source_accounts
- watch_targets
- events
- notifications

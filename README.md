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

## B-1 YouTube Poll Job
環境変数 `YOUTUBE_API_KEY` を設定したうえで実行:
```bash
cd backend
export YOUTUBE_API_KEY=xxxxx
python -m app.jobs.youtube_poller
```

- `source_accounts.platform = "youtube"` のレコードを対象に監視
- `events(source, external_event_id)` のユニーク制約で重複登録を防止

## B-2 Twitch Poll Job
環境変数 `TWITCH_CLIENT_ID`, `TWITCH_ACCESS_TOKEN` を設定したうえで実行:
```bash
cd backend
export TWITCH_CLIENT_ID=xxxxx
export TWITCH_ACCESS_TOKEN=xxxxx
python -m app.jobs.twitch_poller
```

- `source_accounts.platform = "twitch"` のレコードを対象に監視
- live中のstreamを取得し、`event_type=stream_live` で `events` に保存
- `events(source, external_event_id)` のユニーク制約で重複登録を防止

## Initial tables
- users
- streamers
- source_accounts
- watch_targets
- events
- notifications

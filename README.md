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
- `POST /device-tokens`
- `GET /device-tokens?user_id={id}`
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

## C-1 Notification Sender Job
FCM通知送信用ジョブ（通知ログは `notifications` テーブルに保存）:
```bash
cd backend
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-service-account.json
python -m app.jobs.notification_sender
```

- `events` と `watch_targets` から未作成通知を生成
- pending通知をFCMへ送信
- 成功時: `notifications.status=sent`, `sent_at` 記録
- 失敗時: `notifications.status=failed`, `error_message` 記録

## C-2 Idempotency / Duplicate Prevention
- DBユニーク制約: `notifications(user_id, event_id)`
- 送信ジョブは pending のみを対象に処理
- 通知生成時は存在チェック + ユニーク制約違反吸収で並列実行時も重複作成を防止

## Initial tables
- users
- streamers
- source_accounts
- watch_targets
- events
- notifications
- device_tokens

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

## Sprint 3: E2Eローカル確認（最短）
```bash
./scripts/run_local_e2e.sh
```

上記で以下を実行します:
- 依存インストール
- DB migration適用
- デモデータ投入（`python -m app.seed_demo`）

※ DB接続先は `DATABASE_URL` で上書きできます（未指定時は localhost の `streamer_notify`）。

その後、API起動して画面を開いて確認:
- `frontend/index.html`
- `frontend/notification-settings.html`
- `frontend/timeline.html`
- `frontend/ops.html`

## Sprint 3-2: Docker起動
```bash
cp .env.example .env
docker compose up -d db
docker compose run --rm migrate
docker compose up -d backend
docker compose exec backend python -m app.seed_demo
```

停止:
```bash
docker compose down
```

注意:
- FCMを使う場合は `secrets/firebase-service-account.json` を配置してください。
- APIキーは `.env` に設定します。

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

## B-3 X Poll Job
環境変数 `X_BEARER_TOKEN` を設定したうえで実行:
```bash
cd backend
export X_BEARER_TOKEN=xxxxx
python -m app.jobs.x_poller
```

- `source_accounts.platform = "x"` のレコードを対象に監視
- `external_id` は `username` または数値 `user_id` の両対応
- 取得イベントは `event_type=post_created` として `events` に保存
- レート制限（HTTP 429）はアカウント単位でカウントし処理継続

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


## D-1 Minimal UI (streamer register)
`frontend/index.html` をブラウザで開くと、配信者登録と一覧表示ができます。

- APIデフォルト: `http://localhost:8000`
- FastAPIを起動してから利用してください

例:
```bash
cd backend
uvicorn app.main:app --reload
```


## D-2 通知設定画面
- API:
  - `POST /notification-preferences`（upsert）
  - `GET /notification-preferences?user_id={id}`
- 画面: `frontend/notification-settings.html`
- 設定単位: `user_id × streamer_id × platform × event_type` の ON/OFF


## D-3 タイムライン画面強化
- API: `GET /events`
  - フィルタ: `source`, `streamer_id`, `limit`
- 画面: `frontend/timeline.html`
  - source / streamer で絞り込み表示

## E-1 監視ダッシュボード（簡易）
- API: `GET /ops/status`
  - sourceごとの `latest_event_at`, `total_events`, 通知件数（pending/sent/failed）を返却
- 画面: `frontend/ops.html`

## E-2 遅延/制限ステータス表示
- DB: `source_status` テーブルで媒体別の最新状態を保持
  - `status`: `ok` / `rate_limited` / `error` / `unknown`
  - `message`, `last_polled_at`, `last_success_at`
- YouTube / Twitch / X の各ポーラー実行時に `source_status` を更新
- `GET /ops/status` で status情報を返却し、`frontend/ops.html` に表示

利用手順:
1. `cd backend && uvicorn app.main:app --reload`
2. `frontend/ops.html` をブラウザで開く

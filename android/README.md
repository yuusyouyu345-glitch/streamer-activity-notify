# Android MVP Skeleton

最小クライアント雛形です（Jetpack Compose）。

## できること
- API (`/streamers`) の取得
- 配信者一覧の表示
- 再読込

## セットアップ
1. Android Studio で `android/` を開く
2. エミュレータ起動（APIサーバはホスト側で `uvicorn` 起動）
3. `BuildConfig.API_BASE_URL` はデフォルト `http://10.0.2.2:8000`

## 今後（次タスク）
- 通知設定画面（`/notification-preferences` 連携）
- タイムライン画面（`/events` 連携）
- FCM トークン登録（`/device-tokens` 連携）

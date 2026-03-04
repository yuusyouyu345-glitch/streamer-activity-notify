from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import DeviceToken, Event, Notification, WatchTarget


def _ensure_notifications(db) -> int:
    """Create pending notifications idempotently.

    Safety for duplicates is provided in two layers:
    1) App-level existence check
    2) DB unique constraint `uq_notifications_user_event`
    """
    created = 0
    events = db.execute(select(Event)).scalars().all()
    for ev in events:
        watchers = db.execute(select(WatchTarget).where(WatchTarget.streamer_id == ev.streamer_id)).scalars().all()
        for w in watchers:
            exists = db.execute(
                select(Notification.id).where(Notification.user_id == w.user_id, Notification.event_id == ev.id)
            ).scalar_one_or_none()
            if exists:
                continue

            try:
                with db.begin_nested():
                    db.add(Notification(user_id=w.user_id, event_id=ev.id, status="pending"))
                    db.flush()
                created += 1
            except IntegrityError:
                # Race-safe: another worker already inserted the same notification.
                pass
    return created


def _load_fcm_client():
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_path:
        return None, "GOOGLE_APPLICATION_CREDENTIALS is not set"

    try:
        import firebase_admin
        from firebase_admin import credentials, messaging
    except Exception as e:
        return None, f"firebase_admin import failed: {e}"

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

    return messaging, None


def _send_pending(db) -> tuple[int, int]:
    sent = 0
    failed = 0

    messaging, fcm_error = _load_fcm_client()

    pending = db.execute(select(Notification).where(Notification.status == "pending")).scalars().all()
    for n in pending:
        event = db.get(Event, n.event_id)
        tokens = db.execute(select(DeviceToken).where(DeviceToken.user_id == n.user_id)).scalars().all()
        if not tokens:
            n.status = "failed"
            n.error_message = "no device tokens"
            failed += 1
            db.flush()
            continue

        if fcm_error:
            n.status = "failed"
            n.error_message = fcm_error
            failed += 1
            db.flush()
            continue

        payload = {}
        if event and event.payload_json:
            try:
                payload = json.loads(event.payload_json)
            except Exception:
                payload = {}

        title = f"[{event.source}] {event.event_type}" if event else "streamer event"
        body = payload.get("title") or "新しいイベントがあります"

        ok = True
        err = None
        for t in tokens:
            try:
                msg = messaging.Message(
                    token=t.token,
                    notification=messaging.Notification(title=title, body=body),
                    data={
                        "event_id": str(n.event_id),
                        "user_id": str(n.user_id),
                        "source": event.source if event else "",
                    },
                )
                messaging.send(msg)
            except Exception as e:
                ok = False
                err = str(e)
                break

        if ok:
            n.status = "sent"
            n.error_message = None
            n.sent_at = datetime.now(timezone.utc)
            sent += 1
        else:
            n.status = "failed"
            n.error_message = err
            failed += 1
        db.flush()

    return sent, failed


def run_once() -> tuple[int, int, int]:
    db = SessionLocal()
    try:
        created = _ensure_notifications(db)
        sent, failed = _send_pending(db)
        db.commit()
        return created, sent, failed
    finally:
        db.close()


if __name__ == "__main__":
    created, sent, failed = run_once()
    print(f"notification sender finished: created={created} sent={sent} failed={failed}")

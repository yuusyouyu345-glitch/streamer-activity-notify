from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Event, Notification, Streamer, User, WatchTarget
from app.jobs.notification_sender import run_once as run_notification_sender


def run(user_id: int = 1, streamer_id: int = 1) -> None:
    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        if not user:
            raise RuntimeError(f"user not found: {user_id}")
        streamer = db.get(Streamer, streamer_id)
        if not streamer:
            raise RuntimeError(f"streamer not found: {streamer_id}")

        wt = (
            db.execute(
                select(WatchTarget).where(WatchTarget.user_id == user_id, WatchTarget.streamer_id == streamer_id)
            )
            .scalars()
            .first()
        )
        if not wt:
            db.add(WatchTarget(user_id=user_id, streamer_id=streamer_id))
            db.flush()

        external_event_id = f"smoke-{uuid.uuid4().hex[:12]}"
        event = Event(
            streamer_id=streamer_id,
            source="youtube",
            event_type="video_published",
            external_event_id=external_event_id,
            payload_json='{"title":"FCM smoke test from backend"}',
            occurred_at=datetime.now(timezone.utc),
        )
        db.add(event)
        db.commit()
        print(f"created event id={event.id} external_event_id={external_event_id}")
    finally:
        db.close()

    created, sent, failed = run_notification_sender()
    print(f"notification_sender result: created={created} sent={sent} failed={failed}")

    db2 = SessionLocal()
    try:
        latest = (
            db2.execute(
                select(Notification)
                .where(Notification.user_id == user_id)
                .order_by(Notification.id.desc())
            )
            .scalars()
            .first()
        )
        if latest:
            print(
                f"latest notification: id={latest.id} status={latest.status} sent_at={latest.sent_at} error={latest.error_message}"
            )
    finally:
        db2.close()


if __name__ == "__main__":
    run()

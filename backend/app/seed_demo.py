from __future__ import annotations

from datetime import datetime, timezone

from app.database import SessionLocal
from app.models import User, Streamer, SourceAccount, WatchTarget, Event


def run() -> None:
    db = SessionLocal()
    try:
        # user
        user = db.query(User).filter(User.name == "demo-user").first()
        if not user:
            user = User(name="demo-user")
            db.add(user)
            db.flush()

        # streamers + source accounts
        defs = [
            ("デモYouTube", "youtube", "UC_x5XG1OV2P6uZZ5FSM9Ttw"),
            ("デモTwitch", "twitch", "ninja"),
            ("デモX", "x", "TwitterDev"),
        ]

        streamer_ids = []
        for display_name, platform, external_id in defs:
            st = db.query(Streamer).filter(Streamer.display_name == display_name).first()
            if not st:
                st = Streamer(display_name=display_name)
                db.add(st)
                db.flush()
            streamer_ids.append(st.id)

            exists = (
                db.query(SourceAccount)
                .filter(SourceAccount.streamer_id == st.id, SourceAccount.platform == platform)
                .first()
            )
            if not exists:
                db.add(SourceAccount(streamer_id=st.id, platform=platform, external_id=external_id))

        # watch targets
        for sid in streamer_ids:
            wt = db.query(WatchTarget).filter(WatchTarget.user_id == user.id, WatchTarget.streamer_id == sid).first()
            if not wt:
                db.add(WatchTarget(user_id=user.id, streamer_id=sid))

        # dummy event for immediate timeline view
        dummy_exists = db.query(Event).filter(Event.source == "youtube", Event.external_event_id == "demo-seed-event-1").first()
        if not dummy_exists:
            db.add(
                Event(
                    streamer_id=streamer_ids[0],
                    source="youtube",
                    event_type="video_published",
                    external_event_id="demo-seed-event-1",
                    payload_json='{"title":"seed demo event"}',
                    occurred_at=datetime.now(timezone.utc),
                )
            )

        db.commit()
        print(f"seed done: user_id={user.id}")
    finally:
        db.close()


if __name__ == "__main__":
    run()

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Event, SourceAccount
from app.jobs.status_updater import update_source_status

TWITCH_API_BASE = "https://api.twitch.tv/helix"


@dataclass
class TwitchLiveEvent:
    stream_id: str
    started_at: datetime
    title: str
    game_name: str | None


def _parse_dt(value: str) -> datetime:
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def fetch_live_stream(user_login: str, client_id: str, access_token: str) -> TwitchLiveEvent | None:
    headers = {
        "Client-Id": client_id,
        "Authorization": f"Bearer {access_token}",
    }
    params = {"user_login": user_login}
    resp = requests.get(f"{TWITCH_API_BASE}/streams", headers=headers, params=params, timeout=20)
    resp.raise_for_status()
    data: dict[str, Any] = resp.json()
    items = data.get("data", [])
    if not items:
        return None

    item = items[0]
    stream_id = item.get("id")
    started_at = item.get("started_at")
    title = item.get("title")
    game_name = item.get("game_name")
    if not (stream_id and started_at and title):
        return None

    return TwitchLiveEvent(
        stream_id=stream_id,
        started_at=_parse_dt(started_at),
        title=title,
        game_name=game_name,
    )


def save_live_event_for_user(db: Session, streamer_id: int, user_login: str, client_id: str, access_token: str) -> int:
    live = fetch_live_stream(user_login, client_id, access_token)
    if not live:
        return 0

    exists = db.execute(
        select(Event.id).where(Event.source == "twitch", Event.external_event_id == live.stream_id)
    ).scalar_one_or_none()
    if exists:
        return 0

    event = Event(
        streamer_id=streamer_id,
        source="twitch",
        event_type="stream_live",
        external_event_id=live.stream_id,
        payload_json=json.dumps(
            {"title": live.title, "game_name": live.game_name, "user_login": user_login},
            ensure_ascii=False,
        ),
        occurred_at=live.started_at,
    )
    db.add(event)
    db.flush()
    return 1


def run_once() -> int:
    client_id = os.getenv("TWITCH_CLIENT_ID")
    access_token = os.getenv("TWITCH_ACCESS_TOKEN")
    if not client_id or not access_token:
        raise RuntimeError("TWITCH_CLIENT_ID and TWITCH_ACCESS_TOKEN are required")

    db = SessionLocal()
    total_created = 0
    try:
        q = select(SourceAccount).where(SourceAccount.platform == "twitch")
        accounts = db.execute(q).scalars().all()
        for acc in accounts:
            total_created += save_live_event_for_user(db, acc.streamer_id, acc.external_id, client_id, access_token)
        update_source_status(db, "twitch", "ok", f"created={total_created}", success=True)
        db.commit()
    except Exception as e:
        db.rollback()
        update_source_status(db, "twitch", "error", str(e)[:300], success=False)
        db.commit()
        raise
    finally:
        db.close()

    return total_created


if __name__ == "__main__":
    created = run_once()
    print(f"twitch poll finished: created_events={created}")

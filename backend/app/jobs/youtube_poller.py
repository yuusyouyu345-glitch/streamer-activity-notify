from __future__ import annotations

import os
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Event, SourceAccount

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


@dataclass
class YouTubeVideoEvent:
    video_id: str
    published_at: datetime
    title: str


def _parse_dt(value: str) -> datetime:
    # example: 2026-03-03T12:34:56Z
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def fetch_latest_videos(channel_id: str, api_key: str, max_results: int = 5) -> list[YouTubeVideoEvent]:
    params = {
        "part": "snippet",
        "channelId": channel_id,
        "maxResults": max_results,
        "order": "date",
        "type": "video",
        "key": api_key,
    }
    resp = requests.get(f"{YOUTUBE_API_BASE}/search", params=params, timeout=20)
    resp.raise_for_status()
    data: dict[str, Any] = resp.json()

    events: list[YouTubeVideoEvent] = []
    for item in data.get("items", []):
        id_obj = item.get("id", {})
        snippet = item.get("snippet", {})
        video_id = id_obj.get("videoId")
        published_at = snippet.get("publishedAt")
        title = snippet.get("title")
        if not (video_id and published_at and title):
            continue
        events.append(
            YouTubeVideoEvent(
                video_id=video_id,
                published_at=_parse_dt(published_at),
                title=title,
            )
        )
    return events


def save_events_for_channel(db: Session, streamer_id: int, source_account_external_id: str, api_key: str) -> int:
    created = 0
    events = fetch_latest_videos(source_account_external_id, api_key)

    for ev in events:
        exists = db.execute(
            select(Event.id).where(Event.source == "youtube", Event.external_event_id == ev.video_id)
        ).scalar_one_or_none()
        if exists:
            continue

        event = Event(
            streamer_id=streamer_id,
            source="youtube",
            event_type="video_published",
            external_event_id=ev.video_id,
            payload_json=json.dumps({"title": ev.title, "channel_id": source_account_external_id}, ensure_ascii=False),
            occurred_at=ev.published_at,
        )
        db.add(event)
        db.flush()
        created += 1
    return created


def run_once() -> int:
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError("YOUTUBE_API_KEY is required")

    db = SessionLocal()
    total_created = 0
    try:
        q = select(SourceAccount).where(SourceAccount.platform == "youtube")
        accounts = db.execute(q).scalars().all()
        for acc in accounts:
            total_created += save_events_for_channel(db, acc.streamer_id, acc.external_id, api_key)
            db.commit()
    finally:
        db.close()

    return total_created


if __name__ == "__main__":
    created = run_once()
    print(f"youtube poll finished: created_events={created}")

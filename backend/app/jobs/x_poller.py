from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

import requests
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Event, SourceAccount
from app.jobs.status_updater import update_source_status

X_API_BASE = "https://api.twitter.com/2"


class XApiError(RuntimeError):
    pass


def _parse_dt(value: str) -> datetime:
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _headers(bearer_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {bearer_token}"}


def _resolve_user_id(external_id: str, bearer_token: str) -> str:
    # external_id supports both numeric user id and username.
    if external_id.isdigit():
        return external_id

    resp = requests.get(
        f"{X_API_BASE}/users/by/username/{external_id}",
        headers=_headers(bearer_token),
        timeout=20,
    )
    if resp.status_code == 429:
        raise XApiError("rate_limited")
    if not resp.ok:
        raise XApiError(f"resolve_user_failed:{resp.status_code}:{resp.text[:200]}")

    data: dict[str, Any] = resp.json()
    user = data.get("data") or {}
    user_id = user.get("id")
    if not user_id:
        raise XApiError("user_not_found")
    return user_id


def fetch_latest_posts(user_id: str, bearer_token: str, max_results: int = 10) -> list[dict[str, Any]]:
    params = {
        "max_results": str(max_results),
        "tweet.fields": "created_at,text",
        # avoid duplicating replies/retweets in MVP
        "exclude": "replies,retweets",
    }
    resp = requests.get(
        f"{X_API_BASE}/users/{user_id}/tweets",
        headers=_headers(bearer_token),
        params=params,
        timeout=20,
    )
    if resp.status_code == 429:
        raise XApiError("rate_limited")
    if not resp.ok:
        raise XApiError(f"fetch_tweets_failed:{resp.status_code}:{resp.text[:200]}")

    payload: dict[str, Any] = resp.json()
    return payload.get("data", []) or []


def save_posts_for_account(db, streamer_id: int, external_id: str, bearer_token: str) -> int:
    created = 0
    user_id = _resolve_user_id(external_id, bearer_token)
    tweets = fetch_latest_posts(user_id, bearer_token)

    for t in tweets:
        tweet_id = t.get("id")
        text = t.get("text")
        created_at = t.get("created_at")
        if not (tweet_id and created_at):
            continue

        exists = db.execute(
            select(Event.id).where(Event.source == "x", Event.external_event_id == tweet_id)
        ).scalar_one_or_none()
        if exists:
            continue

        db.add(
            Event(
                streamer_id=streamer_id,
                source="x",
                event_type="post_created",
                external_event_id=tweet_id,
                payload_json=json.dumps(
                    {
                        "text": text,
                        "user_id": user_id,
                        "external_id": external_id,
                        "url": f"https://x.com/i/web/status/{tweet_id}",
                    },
                    ensure_ascii=False,
                ),
                occurred_at=_parse_dt(created_at),
            )
        )
        db.flush()
        created += 1

    return created


def run_once() -> tuple[int, int, int]:
    bearer_token = os.getenv("X_BEARER_TOKEN")
    if not bearer_token:
        raise RuntimeError("X_BEARER_TOKEN is required")

    db = SessionLocal()
    total_created = 0
    rate_limited = 0
    failed = 0

    try:
        accounts = db.execute(select(SourceAccount).where(SourceAccount.platform == "x")).scalars().all()
        for acc in accounts:
            try:
                total_created += save_posts_for_account(db, acc.streamer_id, acc.external_id, bearer_token)
            except XApiError as e:
                if str(e) == "rate_limited":
                    rate_limited += 1
                else:
                    failed += 1

        if rate_limited > 0:
            update_source_status(db, "x", "rate_limited", f"rate_limited_accounts={rate_limited}", success=False)
        elif failed > 0:
            update_source_status(db, "x", "error", f"failed_accounts={failed}", success=False)
        else:
            update_source_status(db, "x", "ok", f"created={total_created}", success=True)
        db.commit()
    except Exception as e:
        db.rollback()
        update_source_status(db, "x", "error", str(e)[:300], success=False)
        db.commit()
        raise
    finally:
        db.close()

    return total_created, rate_limited, failed


if __name__ == "__main__":
    created, rate_limited, failed = run_once()
    print(
        f"x poll finished: created_events={created} rate_limited_accounts={rate_limited} failed_accounts={failed}"
    )

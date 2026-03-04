from __future__ import annotations

from datetime import datetime, timezone

from app.models import SourceStatus


def update_source_status(db, source: str, state: str, message: str | None = None, success: bool = False) -> None:
    now = datetime.now(timezone.utc)
    row = db.query(SourceStatus).filter(SourceStatus.source == source).first()
    if not row:
        row = SourceStatus(
            source=source,
            status=state,
            message=message,
            last_polled_at=now,
            last_success_at=now if success else None,
        )
        db.add(row)
        db.flush()
        return

    row.status = state
    row.message = message
    row.last_polled_at = now
    if success:
        row.last_success_at = now
    db.flush()

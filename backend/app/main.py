from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .database import SessionLocal
from .models import Streamer, SourceAccount, WatchTarget, User, DeviceToken
from .schemas import (
    UserCreate,
    UserOut,
    StreamerCreate,
    StreamerOut,
    DeviceTokenCreate,
    DeviceTokenOut,
    WatchTargetCreate,
    WatchTargetOut,
)

app = FastAPI(title="streamer-activity-notify API", version="0.1.0")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = User(name=payload.name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id.desc()).all()


@app.post("/streamers", response_model=StreamerOut, status_code=status.HTTP_201_CREATED)
def create_streamer(payload: StreamerCreate, db: Session = Depends(get_db)):
    streamer = Streamer(display_name=payload.display_name)
    db.add(streamer)
    db.flush()

    for acc in payload.source_accounts:
        db.add(
            SourceAccount(
                streamer_id=streamer.id,
                platform=acc.platform.value,
                external_id=acc.external_id,
            )
        )

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail="duplicate source account or invalid payload") from e

    db.refresh(streamer)
    return streamer


@app.get("/streamers", response_model=list[StreamerOut])
def list_streamers(db: Session = Depends(get_db)):
    return db.query(Streamer).order_by(Streamer.id.desc()).all()


@app.post("/device-tokens", response_model=DeviceTokenOut, status_code=status.HTTP_201_CREATED)
def create_device_token(payload: DeviceTokenCreate, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    row = DeviceToken(user_id=payload.user_id, token=payload.token, platform=payload.platform)
    db.add(row)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail="device token already exists") from e

    db.refresh(row)
    return row


@app.get("/device-tokens", response_model=list[DeviceTokenOut])
def list_device_tokens(user_id: int = Query(...), db: Session = Depends(get_db)):
    return db.query(DeviceToken).filter(DeviceToken.user_id == user_id).order_by(DeviceToken.id.desc()).all()


@app.post("/watch-targets", response_model=WatchTargetOut, status_code=status.HTTP_201_CREATED)
def create_watch_target(payload: WatchTargetCreate, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    streamer = db.get(Streamer, payload.streamer_id)
    if not streamer:
        raise HTTPException(status_code=404, detail="streamer not found")

    record = WatchTarget(user_id=payload.user_id, streamer_id=payload.streamer_id)
    db.add(record)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail="watch target already exists") from e

    db.refresh(record)
    return record


@app.get("/watch-targets", response_model=list[WatchTargetOut])
def list_watch_targets(user_id: int = Query(...), db: Session = Depends(get_db)):
    return (
        db.query(WatchTarget)
        .filter(WatchTarget.user_id == user_id)
        .order_by(WatchTarget.id.desc())
        .all()
    )


@app.delete("/watch-targets/{watch_target_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watch_target(watch_target_id: int, db: Session = Depends(get_db)):
    item = db.get(WatchTarget, watch_target_id)
    if not item:
        raise HTTPException(status_code=404, detail="watch target not found")

    db.delete(item)
    db.commit()
    return None

from enum import Enum
from pydantic import BaseModel, Field, field_validator
import re


class Platform(str, Enum):
    x = "x"
    youtube = "youtube"
    twitch = "twitch"


EXTERNAL_ID_RE = re.compile(r"^[A-Za-z0-9_\-.]{1,255}$")


class SourceAccountCreate(BaseModel):
    platform: Platform
    external_id: str = Field(min_length=1, max_length=255)

    @field_validator("external_id")
    @classmethod
    def validate_external_id(cls, v: str) -> str:
        if not EXTERNAL_ID_RE.match(v):
            raise ValueError("external_id must be URL-safe id (alnum, _, -, .)")
        return v


class StreamerCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=255)
    source_accounts: list[SourceAccountCreate] = Field(default_factory=list)


class StreamerOut(BaseModel):
    id: int
    display_name: str

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    name: str | None = Field(default=None, max_length=255)


class UserOut(BaseModel):
    id: int
    name: str | None

    class Config:
        from_attributes = True


class WatchTargetCreate(BaseModel):
    user_id: int
    streamer_id: int


class WatchTargetOut(BaseModel):
    id: int
    user_id: int
    streamer_id: int

    class Config:
        from_attributes = True

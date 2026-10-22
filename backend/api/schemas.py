"""Pydantic schemas for API request/response bodies.

Kept separate from the SQLAlchemy models (backend/database/models.py) so the
API's public shape can evolve independently of the DB schema.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: int
    discord_id: int
    username: str
    display_name: str
    is_committee: bool

    class Config:
        from_attributes = True


class UserEditIn(BaseModel):
    display_name: Optional[str] = None
    is_committee: Optional[bool] = None


class LeaderboardEntry(BaseModel):
    rank: int
    user: UserOut
    points: int


class LeaderboardOut(BaseModel):
    competition: str
    entries: list[LeaderboardEntry]


class CompetitionOut(BaseModel):
    id: int
    name: str
    description: str
    status: str
    winner_user_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class CompetitionIn(BaseModel):
    name: str
    description: str = ""


class CompetitionEditIn(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class PointsAdjustIn(BaseModel):
    discord_id: int = Field(..., description="Discord user ID of the member")
    username: str = Field(..., description="Discord username, e.g. alex#0001")
    display_name: str = Field(..., description="Member's display name")
    amount: int = Field(..., description="Points to add (negative to remove)")
    reason: str = ""
    competition_name: Optional[str] = Field(
        None, description="Defaults to the current active competition if omitted"
    )


class PointsAdjustOut(BaseModel):
    discord_id: int
    new_total: int
    competition: str
    newly_earned_achievements: list[str] = []


class AnimeOut(BaseModel):
    mal_id: int
    title: str
    description: str
    score: Optional[float]
    episodes: Optional[int]
    status: str
    genres: list[str]
    image_url: str
    mal_url: str


class AnnouncementIn(BaseModel):
    title: str
    message: str
    author_discord_id: int
    channel_id: int
    scheduled_for: Optional[datetime] = Field(
        None, description="If set, the announcement is queued instead of posted immediately"
    )


class AnnouncementEditIn(BaseModel):
    title: Optional[str] = None
    message: Optional[str] = None
    scheduled_for: Optional[datetime] = None


class AnnouncementOut(BaseModel):
    id: int
    title: str
    message: str
    author_discord_id: int
    channel_id: int
    status: str
    scheduled_for: Optional[datetime]
    created_at: datetime
    edited_at: Optional[datetime]

    class Config:
        from_attributes = True


class EventIn(BaseModel):
    name: str
    description: str = ""
    location: str = ""
    event_time: datetime
    channel_id: int
    created_by_discord_id: int
    reminder_minutes_before: int = 60


class EventOut(BaseModel):
    id: int
    name: str
    description: str
    location: str
    event_time: datetime
    channel_id: int
    reminder_minutes_before: int
    reminder_sent: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AchievementOut(BaseModel):
    key: str
    name: str
    description: str
    emoji: str
    earned: bool = False

    class Config:
        from_attributes = True


class AchievementIn(BaseModel):
    key: str = Field(..., description="Short unique slug, e.g. 'night_owl'")
    name: str
    description: str
    emoji: str = "🏆"


class AchievementEditIn(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    emoji: Optional[str] = None


class AchievementAwardIn(BaseModel):
    discord_id: int
    username: str
    display_name: str


class ScoreOut(BaseModel):
    id: int
    competition_id: int
    competition_name: str
    user_id: int
    user_display_name: str
    points: int
    reason: str
    created_at: datetime

    class Config:
        from_attributes = True


class ScoreEditIn(BaseModel):
    points: Optional[int] = None
    reason: Optional[str] = None


class EventEditIn(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    event_time: Optional[datetime] = None
    reminder_minutes_before: Optional[int] = None

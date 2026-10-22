"""SQLAlchemy ORM models for the BAS Bot database."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    """Naive UTC "now". We deliberately strip tzinfo everywhere so every
    datetime in the DB is naive-but-UTC and comparisons never mix aware
    and naive values (SQLite has no real datetime/tz type, so round-tripping
    an aware datetime through it silently comes back naive anyway)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_naive_utc(dt: datetime) -> datetime:
    """Normalizes any datetime (aware or naive) to naive UTC before it goes
    into the DB, so it compares correctly against utcnow() and against
    values that already round-tripped through SQLite."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    discord_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100))
    display_name: Mapped[str] = mapped_column(String(100))
    is_committee: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    scores: Mapped[list["Score"]] = relationship(back_populates="user")

    @property
    def total_points(self) -> int:
        return sum(s.points for s in self.scores)


class Competition(Base):
    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="open")  # open | closed
    winner_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    scores: Mapped[list["Score"]] = relationship(back_populates="competition")


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    points: Mapped[int] = mapped_column(Integer, default=0)
    reason: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    competition: Mapped["Competition"] = relationship(back_populates="scores")
    user: Mapped["User"] = relationship(back_populates="scores")

    @property
    def user_display_name(self) -> str:
        return self.user.display_name if self.user else "(unknown member)"

    @property
    def competition_name(self) -> str:
        return self.competition.name if self.competition else "(unknown competition)"


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    author_discord_id: Mapped[int] = mapped_column(Integer)
    channel_id: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="posted")
    # posted   -> already sent to Discord (or logged after being sent)
    # scheduled -> waiting for scheduled_for, not sent yet
    # cancelled -> scheduled but pulled before it went out
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class Event(Base):
    """A society event (anime night, meeting, competition final, etc.)
    that the bot can list with /events and remind people about."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    location: Mapped[str] = mapped_column(String(200), default="")
    event_time: Mapped[datetime] = mapped_column(DateTime)
    channel_id: Mapped[int] = mapped_column(Integer)
    created_by_discord_id: Mapped[int] = mapped_column(Integer)
    reminder_minutes_before: Mapped[int] = mapped_column(Integer, default=60)
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Achievement(Base):
    """A badge definition, e.g. 'First Blood' for winning your first
    competition. Seeded once at startup -- see services/achievement_service.py."""

    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(200))
    emoji: Mapped[str] = mapped_column(String(10), default="🏆")

    user_links: Mapped[list["UserAchievement"]] = relationship(back_populates="achievement")


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievements.id"))
    earned_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped["User"] = relationship()
    achievement: Mapped["Achievement"] = relationship(back_populates="user_links")


class AnimeCache(Base):
    """Local cache of anime looked up via the Jikan (MyAnimeList) API,
    so repeated searches don't hit the external API every time."""

    __tablename__ = "anime_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mal_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    episodes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="")
    genres: Mapped[str] = mapped_column(String(300), default="")  # comma-separated
    image_url: Mapped[str] = mapped_column(String(300), default="")
    mal_url: Mapped[str] = mapped_column(String(300), default="")
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

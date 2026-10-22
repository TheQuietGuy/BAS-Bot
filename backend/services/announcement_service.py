"""Business logic for announcements: posting immediately, scheduling for
later, editing, and cancelling. Shared by the bot and the API.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import Announcement, to_naive_utc, utcnow


def log_posted_announcement(
    session: Session, title: str, message: str, author_discord_id: int, channel_id: int
) -> Announcement:
    """Records an announcement that has already been sent to Discord."""
    row = Announcement(
        title=title,
        message=message,
        author_discord_id=author_discord_id,
        channel_id=channel_id,
        status="posted",
    )
    session.add(row)
    session.commit()
    return row


def schedule_announcement(
    session: Session,
    title: str,
    message: str,
    author_discord_id: int,
    channel_id: int,
    scheduled_for: datetime,
) -> Announcement:
    row = Announcement(
        title=title,
        message=message,
        author_discord_id=author_discord_id,
        channel_id=channel_id,
        status="scheduled",
        scheduled_for=to_naive_utc(scheduled_for),
    )
    session.add(row)
    session.commit()
    return row


def get_due_scheduled(session: Session) -> list[Announcement]:
    """Scheduled announcements whose time has come, oldest first."""
    now = utcnow()
    return list(
        session.scalars(
            select(Announcement)
            .where(Announcement.status == "scheduled", Announcement.scheduled_for <= now)
            .order_by(Announcement.scheduled_for.asc())
        )
    )


def mark_posted(session: Session, announcement: Announcement) -> None:
    announcement.status = "posted"
    session.commit()


def cancel_announcement(session: Session, announcement: Announcement) -> None:
    announcement.status = "cancelled"
    session.commit()


def edit_announcement(
    session: Session,
    announcement: Announcement,
    title: Optional[str] = None,
    message: Optional[str] = None,
    scheduled_for: Optional[datetime] = None,
) -> Announcement:
    if title is not None:
        announcement.title = title
    if message is not None:
        announcement.message = message
    if scheduled_for is not None:
        announcement.scheduled_for = to_naive_utc(scheduled_for)
        if announcement.status == "cancelled":
            announcement.status = "scheduled"  # rescheduling a cancelled one revives it
    announcement.edited_at = utcnow()
    session.commit()
    return announcement


def get_announcement(session: Session, announcement_id: int) -> Optional[Announcement]:
    return session.get(Announcement, announcement_id)


def list_announcements(session: Session, limit: int = 20) -> list[Announcement]:
    return list(
        session.scalars(
            select(Announcement).order_by(Announcement.created_at.desc()).limit(limit)
        )
    )

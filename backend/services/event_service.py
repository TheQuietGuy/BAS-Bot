"""Business logic for society events (anime nights, meetings, finals) and
their Discord reminders."""
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import Event, to_naive_utc, utcnow


def create_event(
    session: Session,
    name: str,
    event_time: datetime,
    channel_id: int,
    created_by_discord_id: int,
    description: str = "",
    location: str = "",
    reminder_minutes_before: int = 60,
) -> Event:
    event = Event(
        name=name,
        description=description,
        location=location,
        event_time=to_naive_utc(event_time),
        channel_id=channel_id,
        created_by_discord_id=created_by_discord_id,
        reminder_minutes_before=reminder_minutes_before,
    )
    session.add(event)
    session.commit()
    return event


def list_upcoming_events(session: Session, limit: int = 10) -> list[Event]:
    now = utcnow()
    return list(
        session.scalars(
            select(Event).where(Event.event_time >= now).order_by(Event.event_time.asc()).limit(limit)
        )
    )


def get_due_reminders(session: Session) -> list[Event]:
    """Events whose reminder window has arrived but hasn't been sent yet."""
    now = utcnow()
    events = session.scalars(
        select(Event).where(Event.reminder_sent.is_(False), Event.event_time >= now)
    ).all()
    due = []
    for event in events:
        remind_at = event.event_time - timedelta(minutes=event.reminder_minutes_before)
        if now >= remind_at:
            due.append(event)
    return due


def mark_reminder_sent(session: Session, event: Event) -> None:
    event.reminder_sent = True
    session.commit()


def delete_event(session: Session, event: Event) -> None:
    session.delete(event)
    session.commit()


def get_event(session: Session, event_id: int) -> Optional[Event]:
    return session.get(Event, event_id)


def update_event(
    session: Session,
    event: Event,
    name: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    event_time: Optional[datetime] = None,
    reminder_minutes_before: Optional[int] = None,
) -> Event:
    if name is not None:
        event.name = name
    if description is not None:
        event.description = description
    if location is not None:
        event.location = location
    if event_time is not None:
        event.event_time = to_naive_utc(event_time)
        event.reminder_sent = False  # time changed -- reminder window needs re-checking
    if reminder_minutes_before is not None:
        event.reminder_minutes_before = reminder_minutes_before
    session.commit()
    return event

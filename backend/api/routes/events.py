from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth import require_committee
from backend.api.schemas import EventEditIn, EventIn, EventOut
from backend.database.database import get_session
from backend.services import event_service as ev

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=list[EventOut])
def list_events(limit: int = 10):
    with get_session() as session:
        return ev.list_upcoming_events(session, limit=limit)


@router.post("", response_model=EventOut, dependencies=[Depends(require_committee)])
def create_event(body: EventIn):
    with get_session() as session:
        return ev.create_event(
            session,
            name=body.name,
            event_time=body.event_time,
            channel_id=body.channel_id,
            created_by_discord_id=body.created_by_discord_id,
            description=body.description,
            location=body.location,
            reminder_minutes_before=body.reminder_minutes_before,
        )


@router.patch("/{event_id}", response_model=EventOut, dependencies=[Depends(require_committee)])
def edit_event(event_id: int, body: EventEditIn):
    with get_session() as session:
        row = ev.get_event(session, event_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Event not found")
        return ev.update_event(
            session,
            row,
            name=body.name,
            description=body.description,
            location=body.location,
            event_time=body.event_time,
            reminder_minutes_before=body.reminder_minutes_before,
        )


@router.delete("/{event_id}", dependencies=[Depends(require_committee)])
def delete_event(event_id: int):
    with get_session() as session:
        row = ev.get_event(session, event_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Event not found")
        ev.delete_event(session, row)
    return {"deleted": event_id}

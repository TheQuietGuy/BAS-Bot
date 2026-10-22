from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth import require_committee
from backend.api.schemas import AnnouncementEditIn, AnnouncementIn, AnnouncementOut
from backend.database.database import get_session
from backend.services import announcement_service as ann

router = APIRouter(prefix="/api/announcements", tags=["announcements"])


@router.get("", response_model=list[AnnouncementOut])
def list_announcements(limit: int = 20):
    with get_session() as session:
        return ann.list_announcements(session, limit=limit)


@router.post("", response_model=AnnouncementOut, dependencies=[Depends(require_committee)])
def create_announcement(body: AnnouncementIn):
    """Logs an announcement. If `scheduled_for` is set it's queued for the
    bot's scheduler to post later; otherwise it's just recorded as posted
    (actually sending to Discord right now still goes through the bot's
    /announce command, which has the live Discord connection)."""
    with get_session() as session:
        if body.scheduled_for:
            return ann.schedule_announcement(
                session, body.title, body.message, body.author_discord_id,
                body.channel_id, body.scheduled_for,
            )
        return ann.log_posted_announcement(
            session, body.title, body.message, body.author_discord_id, body.channel_id
        )


@router.patch("/{announcement_id}", response_model=AnnouncementOut, dependencies=[Depends(require_committee)])
def edit_announcement(announcement_id: int, body: AnnouncementEditIn):
    with get_session() as session:
        row = ann.get_announcement(session, announcement_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Announcement not found")
        return ann.edit_announcement(
            session, row, title=body.title, message=body.message, scheduled_for=body.scheduled_for
        )


@router.delete("/{announcement_id}", dependencies=[Depends(require_committee)])
def cancel_announcement(announcement_id: int):
    """Cancels a still-scheduled announcement. Already-posted ones are kept
    as history rather than deleted."""
    with get_session() as session:
        row = ann.get_announcement(session, announcement_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Announcement not found")
        if row.status != "scheduled":
            raise HTTPException(
                status_code=400, detail="Only scheduled announcements can be cancelled."
            )
        ann.cancel_announcement(session, row)
    return {"cancelled": announcement_id}

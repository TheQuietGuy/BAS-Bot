from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from backend.api.auth import require_committee
from backend.api.schemas import AchievementAwardIn, AchievementEditIn, AchievementIn, AchievementOut
from backend.database.database import get_session
from backend.services import achievement_service as ach
from backend.services import leaderboard_service as lb

router = APIRouter(prefix="/api/achievements", tags=["achievements"])


@router.get("", response_model=list[AchievementOut])
def list_achievements(
    discord_id: Optional[int] = Query(None, description="Mark which ones this member has earned")
):
    with get_session() as session:
        all_achievements = ach.list_all_achievements(session)
        earned_keys: set[str] = set()

        if discord_id is not None:
            user = lb.get_user_by_discord_id(session, discord_id)
            if user:
                earned_keys = {a.key for a in ach.list_user_achievements(session, user)}

        return [
            AchievementOut(
                key=a.key,
                name=a.name,
                description=a.description,
                emoji=a.emoji,
                earned=a.key in earned_keys,
            )
            for a in all_achievements
        ]


@router.post("", response_model=AchievementOut, dependencies=[Depends(require_committee)])
def create_achievement(body: AchievementIn):
    with get_session() as session:
        if ach.get_achievement_by_key(session, body.key):
            raise HTTPException(status_code=409, detail=f"'{body.key}' already exists")
        return ach.create_achievement(session, body.key, body.name, body.description, body.emoji)


@router.patch("/{key}", response_model=AchievementOut, dependencies=[Depends(require_committee)])
def edit_achievement(key: str, body: AchievementEditIn):
    with get_session() as session:
        achievement = ach.get_achievement_by_key(session, key)
        if achievement is None:
            raise HTTPException(status_code=404, detail="Achievement not found")
        return ach.update_achievement(
            session, achievement, name=body.name, description=body.description, emoji=body.emoji
        )


@router.delete("/{key}", dependencies=[Depends(require_committee)])
def delete_achievement(key: str):
    with get_session() as session:
        achievement = ach.get_achievement_by_key(session, key)
        if achievement is None:
            raise HTTPException(status_code=404, detail="Achievement not found")
        ach.delete_achievement(session, achievement)
    return {"deleted": key}


@router.post("/{key}/award", dependencies=[Depends(require_committee)])
def award_achievement(key: str, body: AchievementAwardIn):
    """Committee override: manually grants an achievement to a member,
    bypassing the normal earn conditions."""
    with get_session() as session:
        achievement = ach.get_achievement_by_key(session, key)
        if achievement is None:
            raise HTTPException(status_code=404, detail="Achievement not found")
        user = lb.get_or_create_user(session, body.discord_id, body.username, body.display_name)
        newly_awarded = ach.manually_award(session, user, achievement)
    return {"discord_id": body.discord_id, "achievement": key, "newly_awarded": newly_awarded}


@router.delete("/{key}/award/{discord_id}", dependencies=[Depends(require_committee)])
def revoke_achievement(key: str, discord_id: int):
    with get_session() as session:
        achievement = ach.get_achievement_by_key(session, key)
        if achievement is None:
            raise HTTPException(status_code=404, detail="Achievement not found")
        user = lb.get_user_by_discord_id(session, discord_id)
        if user is None:
            raise HTTPException(status_code=404, detail="Member not found")
        revoked = ach.revoke_achievement(session, user, achievement)
    return {"discord_id": discord_id, "achievement": key, "revoked": revoked}

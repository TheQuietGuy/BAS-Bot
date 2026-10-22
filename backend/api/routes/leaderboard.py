from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from backend.api.auth import require_committee
from backend.api.schemas import (
    CompetitionEditIn,
    CompetitionIn,
    CompetitionOut,
    LeaderboardEntry,
    LeaderboardOut,
    PointsAdjustIn,
    PointsAdjustOut,
    ScoreEditIn,
    ScoreOut,
    UserEditIn,
    UserOut,
)
from backend.database.database import get_session
from backend.services import achievement_service as ach
from backend.services import leaderboard_service as lb
from backend.services import leaderboard_notify as notify

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


@router.get("/competitions", response_model=list[CompetitionOut])
def list_competitions():
    with get_session() as session:
        return lb.list_competitions(session)


@router.post(
    "/competitions", response_model=CompetitionOut, dependencies=[Depends(require_committee)]
)
def create_competition(body: CompetitionIn):
    """Creates a new open competition directly, without closing the current
    one (unlike /reset)."""
    with get_session() as session:
        return lb.create_competition(session, body.name, body.description)


@router.patch(
    "/competitions/{competition_id}",
    response_model=CompetitionOut,
    dependencies=[Depends(require_committee)],
)
def edit_competition(competition_id: int, body: CompetitionEditIn):
    with get_session() as session:
        comp = lb.get_competition_by_id(session, competition_id)
        if comp is None:
            raise HTTPException(status_code=404, detail="Competition not found")
        return lb.update_competition(
            session, comp, name=body.name, description=body.description, status=body.status
        )


@router.delete(
    "/competitions/{competition_id}", dependencies=[Depends(require_committee)]
)
def delete_competition(competition_id: int):
    """Deletes a competition and every score logged under it. No undo."""
    with get_session() as session:
        comp = lb.get_competition_by_id(session, competition_id)
        if comp is None:
            raise HTTPException(status_code=404, detail="Competition not found")
        lb.delete_competition(session, comp)
    return {"deleted": competition_id}


@router.get("/scores", response_model=list[ScoreOut])
def list_scores(competition_id: Optional[int] = None, user_id: Optional[int] = None, limit: int = 50):
    with get_session() as session:
        return lb.list_scores(session, competition_id=competition_id, user_id=user_id, limit=limit)


@router.patch(
    "/scores/{score_id}", response_model=ScoreOut, dependencies=[Depends(require_committee)]
)
async def edit_score(score_id: int, body: ScoreEditIn):
    with get_session() as session:
        score = lb.get_score_by_id(session, score_id)
        if score is None:
            raise HTTPException(status_code=404, detail="Score entry not found")
        updated = lb.update_score(session, score, points=body.points, reason=body.reason)
        name, points, comp_name = updated.user_display_name, updated.points, updated.competition_name

    await notify.notify_leaderboard_update(
        "📝 Score corrected",
        f"**{name}**'s entry in *{comp_name}* was updated to **{points}** points.",
    )
    return updated


@router.delete("/scores/{score_id}", dependencies=[Depends(require_committee)])
async def delete_score(score_id: int):
    with get_session() as session:
        score = lb.get_score_by_id(session, score_id)
        if score is None:
            raise HTTPException(status_code=404, detail="Score entry not found")
        name, comp_name = score.user_display_name, score.competition_name
        lb.delete_score(session, score)

    await notify.notify_leaderboard_update(
        "🗑️ Score entry removed",
        f"An entry for **{name}** in *{comp_name}* was deleted.",
        colour=0xD6432F,
    )
    return {"deleted": score_id}


@router.get("/users", response_model=list[UserOut])
def list_users():
    with get_session() as session:
        return lb.list_users(session)


@router.patch(
    "/users/{user_id}", response_model=UserOut, dependencies=[Depends(require_committee)]
)
def edit_user(user_id: int, body: UserEditIn):
    with get_session() as session:
        user = lb.get_user_by_id(session, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="Member not found")
        return lb.update_user(
            session, user, display_name=body.display_name, is_committee=body.is_committee
        )


@router.get("", response_model=LeaderboardOut)
def get_leaderboard(competition: Optional[str] = None, limit: int = 10):
    with get_session() as session:
        comp = (
            lb.find_competition_by_name(session, competition)
            if competition
            else lb.get_or_create_active_competition(session)
        )
        if comp is None:
            raise HTTPException(status_code=404, detail=f"No competition named '{competition}'")

        ranked = lb.get_leaderboard(session, comp, limit=limit)
        entries = [
            LeaderboardEntry(rank=i + 1, user=UserOut.model_validate(user), points=points)
            for i, (user, points) in enumerate(ranked)
        ]
        return LeaderboardOut(competition=comp.name, entries=entries)


@router.post("/points", response_model=PointsAdjustOut, dependencies=[Depends(require_committee)])
async def adjust_points(body: PointsAdjustIn):
    """Award or remove points for a member. Committee-only (Bearer token)."""
    with get_session() as session:
        user = lb.get_or_create_user(session, body.discord_id, body.username, body.display_name)
        comp = (
            lb.find_competition_by_name(session, body.competition_name)
            if body.competition_name
            else lb.get_or_create_active_competition(session)
        )
        if comp is None:
            raise HTTPException(
                status_code=404, detail=f"No competition named '{body.competition_name}'"
            )

        lb.add_points(session, user, comp, body.amount, body.reason)
        total = lb.get_user_points(session, user, comp)
        newly_earned = ach.check_participation_achievements(session, user)
        display_name = user.display_name

    sign = "+" if body.amount > 0 else ""
    achievement_note = f"\n🎉 Also earned: {', '.join(a.name for a in newly_earned)}" if newly_earned else ""
    await notify.notify_leaderboard_update(
        "🏆 Leaderboard update",
        f"**{display_name}** {sign}{body.amount} pts ({comp.name if comp else ''}) "
        f"— now **{total}** total.{achievement_note}",
    )

    return PointsAdjustOut(
        discord_id=user.discord_id,
        new_total=total,
        competition=comp.name,
        newly_earned_achievements=[a.key for a in newly_earned],
    )


@router.post(
    "/reset", response_model=CompetitionOut, dependencies=[Depends(require_committee)]
)
async def reset_leaderboard(new_name: str = "General"):
    """Close the current competition (recording its winner) and start a
    fresh one. Committee-only."""
    with get_session() as session:
        old = lb.get_or_create_active_competition(session)
        _, winner = lb.close_competition(session, old)
        if winner:
            ach.check_win_achievements(session, winner)
        new_comp = lb.get_or_create_active_competition(session, name=new_name)
        winner_name = winner.display_name if winner else None
        old_name = old.name

    description = f"**{old_name}** closed"
    description += f" — winner: **{winner_name}** 🏆" if winner_name else " (no scores)"
    description += f".\nNew leaderboard open: **{new_comp.name}**"
    await notify.notify_leaderboard_update("🔁 Leaderboard reset", description, colour=0x4C7EF0)

    return new_comp

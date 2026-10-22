"""Business logic for users, competitions and scores.

Kept separate from the Discord command layer so the same functions could
later be reused by a FastAPI backend for the web dashboard (Phase 4/5).
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import Competition, Score, User, utcnow


def get_or_create_user(session: Session, discord_id: int, username: str, display_name: str) -> User:
    user = session.scalar(select(User).where(User.discord_id == discord_id))
    if user is None:
        user = User(discord_id=discord_id, username=username, display_name=display_name)
        session.add(user)
        session.commit()
    else:
        # Keep the cached name fresh in case the member changed it.
        if user.username != username or user.display_name != display_name:
            user.username = username
            user.display_name = display_name
            session.commit()
    return user


def get_or_create_active_competition(session: Session, name: str = "General") -> Competition:
    """Fetches the named open competition, creating it if it doesn't exist yet.
    This lets the bot work out of the box with one default leaderboard."""
    comp = session.scalar(
        select(Competition).where(Competition.name == name, Competition.status == "open")
    )
    if comp is None:
        comp = Competition(name=name, description="Default leaderboard", status="open")
        session.add(comp)
        session.commit()
    return comp


def add_points(session: Session, user: User, competition: Competition, points: int, reason: str = "") -> Score:
    score = Score(user_id=user.id, competition_id=competition.id, points=points, reason=reason)
    session.add(score)
    session.commit()
    return score


def get_leaderboard(session: Session, competition: Competition, limit: int = 10) -> list[tuple[User, int]]:
    """Returns [(user, total_points), ...] sorted descending, for one competition."""
    rows = session.scalars(
        select(Score).where(Score.competition_id == competition.id)
    ).all()

    totals: dict[int, int] = {}
    for row in rows:
        totals[row.user_id] = totals.get(row.user_id, 0) + row.points

    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:limit]

    results = []
    for user_id, total in ranked:
        user = session.get(User, user_id)
        if user:
            results.append((user, total))
    return results


def get_user_points(session: Session, user: User, competition: Competition) -> int:
    rows = session.scalars(
        select(Score).where(Score.user_id == user.id, Score.competition_id == competition.id)
    ).all()
    return sum(r.points for r in rows)


def list_competitions(session: Session) -> list[Competition]:
    return list(session.scalars(select(Competition).order_by(Competition.created_at.desc())))


def find_competition_by_name(session: Session, name: str) -> Optional[Competition]:
    return session.scalar(select(Competition).where(Competition.name.ilike(name)))


def get_user_by_discord_id(session: Session, discord_id: int) -> Optional[User]:
    """Read-only lookup -- unlike get_or_create_user, never creates or
    overwrites a user record. Use this when you don't have a fresh
    username/display_name to hand (e.g. an API query param)."""
    return session.scalar(select(User).where(User.discord_id == discord_id))


def close_competition(session: Session, competition: Competition) -> tuple[Competition, Optional[User]]:
    """Closes a competition and records its winner (highest total points),
    if it had any scores at all. Returns (competition, winner_or_None).

    Callers that care about achievement badges should pass the winner to
    achievement_service.check_win_achievements(session, winner).
    """
    ranked = get_leaderboard(session, competition, limit=1)
    winner = ranked[0][0] if ranked else None

    competition.status = "closed"
    competition.closed_at = utcnow()
    if winner:
        competition.winner_user_id = winner.id
    session.commit()

    return competition, winner


# ---- Users ----

def list_users(session: Session) -> list[User]:
    return list(session.scalars(select(User).order_by(User.display_name)))


def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
    return session.get(User, user_id)


def update_user(
    session: Session,
    user: User,
    display_name: Optional[str] = None,
    is_committee: Optional[bool] = None,
) -> User:
    if display_name is not None:
        user.display_name = display_name
    if is_committee is not None:
        user.is_committee = is_committee
    session.commit()
    return user


# ---- Competitions ----

def create_competition(session: Session, name: str, description: str = "") -> Competition:
    competition = Competition(name=name, description=description, status="open")
    session.add(competition)
    session.commit()
    return competition


def get_competition_by_id(session: Session, competition_id: int) -> Optional[Competition]:
    return session.get(Competition, competition_id)


def update_competition(
    session: Session,
    competition: Competition,
    name: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
) -> Competition:
    if name is not None:
        competition.name = name
    if description is not None:
        competition.description = description
    if status is not None:
        competition.status = status
    session.commit()
    return competition


def delete_competition(session: Session, competition: Competition) -> None:
    """Deletes a competition and every score entry logged under it. There's
    no undo -- the dashboard should confirm with the user before calling this."""
    session.query(Score).filter(Score.competition_id == competition.id).delete()
    session.delete(competition)
    session.commit()


# ---- Individual score entries ----

def list_scores(
    session: Session,
    competition_id: Optional[int] = None,
    user_id: Optional[int] = None,
    limit: int = 50,
) -> list[Score]:
    query = select(Score).order_by(Score.created_at.desc()).limit(limit)
    if competition_id is not None:
        query = query.where(Score.competition_id == competition_id)
    if user_id is not None:
        query = query.where(Score.user_id == user_id)
    scores = list(session.scalars(query))
    for s in scores:
        _ = s.user_display_name  # force-load the relationship while the session is open
        _ = s.competition_name
    return scores


def get_score_by_id(session: Session, score_id: int) -> Optional[Score]:
    return session.get(Score, score_id)


def update_score(
    session: Session, score: Score, points: Optional[int] = None, reason: Optional[str] = None
) -> Score:
    if points is not None:
        score.points = points
    if reason is not None:
        score.reason = reason
    session.commit()
    _ = score.user_display_name
    _ = score.competition_name
    return score


def delete_score(session: Session, score: Score) -> None:
    session.delete(score)
    session.commit()

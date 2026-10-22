"""Achievement badges. Definitions are seeded once at startup; awarding
happens as a side effect of normal actions (points added, competition
closed) rather than on a schedule.
"""
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database.models import Achievement, Competition, Score, User, UserAchievement

# (key, name, description, emoji) -- matches the original project plan's examples.
ACHIEVEMENT_DEFS = [
    ("first_blood", "First Blood", "Win your first competition", "🏆"),
    ("gamer", "Gamer", "Participate in 5 competitions", "🎮"),
    ("champion", "Champion", "Win 3 competitions", "👑"),
]


def seed_achievements(session: Session) -> None:
    """Idempotently make sure every achievement definition exists in the DB."""
    existing_keys = set(session.scalars(select(Achievement.key)).all())
    for key, name, description, emoji in ACHIEVEMENT_DEFS:
        if key not in existing_keys:
            session.add(Achievement(key=key, name=name, description=description, emoji=emoji))
    session.commit()


def _award_if_new(session: Session, user: User, key: str) -> Optional[Achievement]:
    """Awards `key` to `user` if they don't already have it. Returns the
    Achievement if it was newly awarded, else None."""
    achievement = session.scalar(select(Achievement).where(Achievement.key == key))
    if achievement is None:
        return None

    already_has = session.scalar(
        select(UserAchievement).where(
            UserAchievement.user_id == user.id, UserAchievement.achievement_id == achievement.id
        )
    )
    if already_has:
        return None

    session.add(UserAchievement(user_id=user.id, achievement_id=achievement.id))
    session.commit()
    return achievement


def check_participation_achievements(session: Session, user: User) -> list[Achievement]:
    """Call after points are awarded. Checks milestone achievements based on
    how many distinct competitions the member has scored in."""
    newly_earned: list[Achievement] = []

    distinct_competitions = session.scalar(
        select(func.count(func.distinct(Score.competition_id))).where(Score.user_id == user.id)
    )
    if distinct_competitions and distinct_competitions >= 5:
        earned = _award_if_new(session, user, "gamer")
        if earned:
            newly_earned.append(earned)

    return newly_earned


def check_win_achievements(session: Session, user: User) -> list[Achievement]:
    """Call after a competition is closed with `user` as the winner."""
    newly_earned: list[Achievement] = []

    win_count = session.scalar(
        select(func.count(Competition.id)).where(Competition.winner_user_id == user.id)
    )
    if win_count and win_count >= 1:
        earned = _award_if_new(session, user, "first_blood")
        if earned:
            newly_earned.append(earned)
    if win_count and win_count >= 3:
        earned = _award_if_new(session, user, "champion")
        if earned:
            newly_earned.append(earned)

    return newly_earned


def list_user_achievements(session: Session, user: User) -> list[Achievement]:
    rows = session.scalars(
        select(UserAchievement).where(UserAchievement.user_id == user.id)
    ).all()
    return [row.achievement for row in rows]


def list_all_achievements(session: Session) -> list[Achievement]:
    return list(session.scalars(select(Achievement)))


def get_achievement_by_key(session: Session, key: str) -> Optional[Achievement]:
    return session.scalar(select(Achievement).where(Achievement.key == key))


def create_achievement(
    session: Session, key: str, name: str, description: str, emoji: str = "🏆"
) -> Achievement:
    achievement = Achievement(key=key, name=name, description=description, emoji=emoji)
    session.add(achievement)
    session.commit()
    return achievement


def update_achievement(
    session: Session,
    achievement: Achievement,
    name: Optional[str] = None,
    description: Optional[str] = None,
    emoji: Optional[str] = None,
) -> Achievement:
    if name is not None:
        achievement.name = name
    if description is not None:
        achievement.description = description
    if emoji is not None:
        achievement.emoji = emoji
    session.commit()
    return achievement


def delete_achievement(session: Session, achievement: Achievement) -> None:
    """Deletes a custom achievement and every award of it on record."""
    session.query(UserAchievement).filter(
        UserAchievement.achievement_id == achievement.id
    ).delete()
    session.delete(achievement)
    session.commit()


def manually_award(session: Session, user: User, achievement: Achievement) -> bool:
    """Committee override: grants an achievement directly. Returns False if
    the member already has it."""
    already_has = session.scalar(
        select(UserAchievement).where(
            UserAchievement.user_id == user.id, UserAchievement.achievement_id == achievement.id
        )
    )
    if already_has:
        return False
    session.add(UserAchievement(user_id=user.id, achievement_id=achievement.id))
    session.commit()
    return True


def revoke_achievement(session: Session, user: User, achievement: Achievement) -> bool:
    """Committee override: removes an achievement from a member. Returns
    False if they didn't have it."""
    link = session.scalar(
        select(UserAchievement).where(
            UserAchievement.user_id == user.id, UserAchievement.achievement_id == achievement.id
        )
    )
    if link is None:
        return False
    session.delete(link)
    session.commit()
    return True

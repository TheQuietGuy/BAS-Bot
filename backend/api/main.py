"""FastAPI backend for the BAS Bot dashboard.

Run with:
    uvicorn backend.api.main:app --reload --port 8000

This exposes the same leaderboard/anime logic the Discord bot uses
(backend/services/), so the bot and the future React dashboard stay in
sync without duplicated business logic. It talks to the SAME SQLite
database file as the bot -- run them side by side, not instead of each
other.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import achievements, announcements, anime, auth, discord_directory, events, leaderboard
from backend.database.database import get_session, init_db
from backend.services.achievement_service import seed_achievements

app = FastAPI(title="BAS Bot API", version="0.1.0")

# Loosened for local dev (the Vite dashboard runs on a different port).
# Tighten this to the dashboard's real origin before hosting anywhere public.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leaderboard.router)
app.include_router(anime.router)
app.include_router(announcements.router)
app.include_router(auth.router)
app.include_router(events.router)
app.include_router(achievements.router)
app.include_router(discord_directory.router)


@app.on_event("startup")
def on_startup():
    init_db()
    with get_session() as session:
        seed_achievements(session)


@app.get("/api/health")
def health():
    return {"status": "ok"}

# BAS Bot — Brunel Anime Society Discord Bot + API + Dashboard

A locally hosted Discord bot, a FastAPI backend, and a React dashboard for
managing competition leaderboards, announcements, events, achievements,
and anime lookups for the Brunel Anime Society.

This covers the full original project plan: Phase 1 (bot + leaderboard),
Phase 2 (anime search), Phase 3 (scheduled/editable announcements), Phase 4
(FastAPI backend), Phase 5 (React dashboard with real Discord OAuth2
login), and Phase 6 polish (achievements, event reminders, DB backups,
dashboard chart).

**The bot and the API are two separate processes that share one SQLite
database.** Run either alone, or both side by side — they never talk to
each other directly, only through the shared DB.

## Features

**Everyone**
- `/help` — list all commands
- `/leaderboard [competition]` — top 10 members by points
- `/profile [member]` / `/my-points` — points lookup
- `/anime search|random|top` — MyAnimeList lookup via the free Jikan API
- `/events list` — upcoming society events
- `/achievements [member]` — badges earned so far

**Committee only** (checked against Discord role IDs, never usernames)
- `/announce <title> <message> [channel] [when]` — post now, or schedule for later
- `/admin announcement edit|cancel` — fix or pull a logged/scheduled announcement
- `/admin points add|remove` — award/remove leaderboard points (auto-checks achievement unlocks)
- `/admin leaderboard reset` — closes the current competition (recording its winner) and starts a new one
- `/events create|delete` — manage society events; the bot reminds the event's channel automatically

**Achievements** (auto-awarded, mirrors the original project plan)
- 🏆 First Blood — win your first competition
- 🎮 Gamer — participate in 5 competitions
- 👑 Champion — win 3 competitions

## Project structure

```
bas-bot/
├── backend/
│   ├── main.py                  # Discord bot entry point
│   ├── config.py                # reads .env
│   ├── bot/
│   │   ├── bot.py               # Discord client, loads cogs, syncs slash commands
│   │   ├── permissions.py       # committee role check (Discord role IDs)
│   │   ├── scheduler.py         # background loop: posts due announcements + event reminders
│   │   └── commands/            # one cog per feature area
│   ├── api/
│   │   ├── main.py               # FastAPI app entry point
│   │   ├── auth.py                # JWT-based committee check (+ legacy key fallback)
│   │   ├── jwt_utils.py           # session token + OAuth CSRF state signing
│   │   ├── schemas.py             # Pydantic request/response models
│   │   └── routes/                # leaderboard, anime, announcements, events, achievements, auth
│   ├── database/
│   │   ├── models.py              # SQLAlchemy models
│   │   └── database.py            # engine/session setup
│   └── services/                  # business logic shared by the bot AND the API
│       ├── leaderboard_service.py
│       ├── anime_service.py       # Jikan/MyAnimeList wrapper with local caching
│       ├── announcement_service.py
│       ├── event_service.py
│       ├── achievement_service.py
│       └── discord_oauth.py       # OAuth2 code exchange, identity, guild role lookup
├── frontend/                      # React + TypeScript + Tailwind dashboard
├── scripts/
│   └── backup_db.py               # scheduled SQLite backup with retention
├── database/                      # bas.db (SQLite), created on first run
├── requirements.txt
├── .env.example
├── start.sh                       # runs the Discord bot
└── start_api.sh                   # runs the FastAPI backend
```

## Setup

1. **Create a Discord application & bot**
   - https://discord.com/developers/applications → New Application
   - Bot tab → Reset Token → copy it
   - Enable **Server Members Intent** under Privileged Gateway Intents
   - OAuth2 → URL Generator → scopes `bot`, `applications.commands`;
     permissions at least `Send Messages`, `Embed Links`, `Use Slash Commands`
   - Open the generated URL to invite the bot to the society's server

2. **Get your server (guild) ID and committee role ID(s)**
   - Enable Developer Mode (User Settings → Advanced)
   - Right-click the server icon → Copy Server ID
   - Right-click each committee role in Server Settings → Roles → Copy Role ID

3. **Set up Discord OAuth2 for the dashboard** (same application as the bot)
   - OAuth2 tab → note the **Client ID** and **Client Secret**
   - Add a redirect: `http://localhost:8000/api/auth/callback`

4. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   Fill in `DISCORD_TOKEN`, `GUILD_ID`, `COMMITTEE_ROLE_IDS`,
   `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`, and a generated `JWT_SECRET`
   (`python3 -c "import secrets; print(secrets.token_urlsafe(32))"`).

5. **Install dependencies**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

6. **Run the bot**
   ```bash
   ./start.sh
   ```
   With `GUILD_ID` set, slash commands sync to your server instantly
   instead of waiting up to an hour for global sync.

The database is created automatically at `database/bas.db` on first run
(bot or API), achievement definitions included.

## Running the API

```bash
./start_api.sh
# or: uvicorn backend.api.main:app --reload --port 8000
```

Swagger docs at `http://localhost:8000/docs`.

| Route | Method | Auth | Notes |
|---|---|---|---|
| `/api/health` | GET | — | health check |
| `/api/leaderboard` | GET | — | `?competition=`, `?limit=` |
| `/api/leaderboard/competitions` | GET | — | list all competitions |
| `/api/leaderboard/competitions` | POST | committee | create a new open competition directly |
| `/api/leaderboard/competitions/{id}` | PATCH | committee | rename/edit/change status |
| `/api/leaderboard/competitions/{id}` | DELETE | committee | delete it and every score logged under it |
| `/api/leaderboard/points` | POST | committee | award/remove points, returns any newly-earned achievements |
| `/api/leaderboard/reset` | POST | committee | closes current (records winner), opens a new one |
| `/api/leaderboard/scores` | GET | — | raw score log, `?competition_id=`, `?user_id=` |
| `/api/leaderboard/scores/{id}` | PATCH / DELETE | committee | edit or delete one score entry |
| `/api/leaderboard/users` | GET | — | every known member |
| `/api/leaderboard/users/{id}` | PATCH | committee | edit display name / manual committee override |
| `/api/anime/search\|random\|top` | GET | — | MyAnimeList lookup |
| `/api/announcements` | GET | — | history |
| `/api/announcements` | POST | committee | log now, or pass `scheduled_for` to queue it |
| `/api/announcements/{id}` | PATCH | committee | edit title/message |
| `/api/announcements/{id}` | DELETE | committee | cancel a still-scheduled one |
| `/api/events` | GET | — | upcoming events |
| `/api/events` | POST | committee | create |
| `/api/events/{id}` | PATCH / DELETE | committee | edit or remove |
| `/api/achievements` | GET | — | `?discord_id=` marks which ones that member earned |
| `/api/achievements` | POST | committee | create a custom badge |
| `/api/achievements/{key}` | PATCH / DELETE | committee | edit or delete a badge |
| `/api/achievements/{key}/award` | POST | committee | manually grant a badge to a member |
| `/api/achievements/{key}/award/{discord_id}` | DELETE | committee | revoke it |
| `/api/discord/channels` | GET | — | text channels in your server, for the dashboard's channel dropdowns (empty list if Discord can't be reached) |
| `/api/discord/members` | GET | — | non-bot server members, for the dashboard's member pickers (needs the bot's Server Members intent) |
| `/api/auth/login` | GET | — | redirects to Discord's consent screen |
| `/api/auth/callback` | GET | — | Discord redirects here; issues a session token |
| `/api/auth/me` | GET | session token | who you're logged in as |

### Auth: Discord OAuth2 (primary) + legacy key (fallback)

Committee routes check a signed session token issued after a real Discord
login:

1. Dashboard sends the browser to `/api/auth/login`.
2. User approves on Discord's consent screen.
3. Discord redirects to `/api/auth/callback`, which exchanges the code,
   looks up the member's **roles in your guild using the bot's own token**
   (no extra scopes needed from the user), checks them against
   `COMMITTEE_ROLE_IDS`, and issues a signed JWT.
4. The dashboard stores that JWT and sends it as
   `Authorization: Bearer <token>`.

`DASHBOARD_API_KEY` (a shared secret) still works as a fallback so an
older integration doesn't break overnight — leave it blank once you've
switched to OAuth2 login.

**Testing note:** this environment's outbound network couldn't reach
`discord.com`, so the actual code-exchange/identity/role-lookup HTTP calls
in `discord_oauth.py` are untested against live Discord — worth a real
login test once this is running with your Discord app credentials.
Everything downstream of that (JWT issuance and verification, the
committee/non-committee permission split, the `/api/auth/me` route) **was**
tested end-to-end with real signed tokens.

## Background scheduler

The bot runs a one-minute polling loop (`backend/bot/scheduler.py`) that:
- posts any scheduled announcement whose time has arrived
- sends event reminders once their reminder window opens

Verified with a scripted test (mocked Discord channel): correctly posts
only due items, leaves future ones alone, and marks each as sent so it's
never posted twice.

## Database backups

```bash
python3 scripts/backup_db.py            # keeps the last 14 by default
python3 scripts/backup_db.py --keep 30
```

Uses SQLite's own backup API, so it's safe to run while the bot is live.
Sample crontab entry (daily at 3am):
```
0 3 * * * cd /path/to/bas-bot && /path/to/.venv/bin/python3 scripts/backup_db.py
```

## Running the dashboard

```bash
# terminal 1
./start_api.sh

# terminal 2
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Pages: Dashboard (overview + leaderboard
chart), Leaderboard (standings, committee point management, a
Competitions panel to create/rename/delete/open-close competitions, and a
raw score-entry log — shown with real member and competition names, not
IDs — you can edit or delete line by line), Members (every known member —
rename, toggle committee status manually), Anime (search/random/top, now
with poster thumbnails and click-through from the top list), Announcements
(history, scheduling, rescheduling, inline edit, cancel), Events
(upcoming, committee create + inline edit + remove), Achievements (badge
grid; committee can create custom badges, edit or delete existing ones,
and manually award/revoke a badge for any member), Settings (Discord
login/logout, leaderboard reset).

Forms use real Discord names instead of raw IDs: announcements and events pick a channel from a dropdown, and awarding points or badges picks a member by typing part of their name. Destructive actions (deleting a competition, score entry, badge or event, cancelling a scheduled announcement) ask for confirmation first.

Almost everything committee-only in the API now has a matching edit
control in the dashboard, not just create/delete — competitions, score
entries, events, announcements, member records, and achievements can all
be edited in place, not only through the bot's slash commands.

Log in via Settings → "Log in with Discord". Committee actions unlock
automatically if your Discord roles match `COMMITTEE_ROLE_IDS` — no
separate dashboard password.

Design leans into the subject matter rather than a generic admin
template: manga-panel-style bordered blocks (hairline rules, near-zero
radius, no drop shadows) instead of soft rounded cards, a mincho display
face for headings paired with a geometric sans for the UI, and an
asymmetric dashboard hero instead of identical stat tiles.

**Verified:** `npm run build` compiles cleanly (full TypeScript check +
Vite build) after every change in this project. Every new API route
behind the dashboard's edit controls (competitions, scores, users,
events, achievements) was exercised end-to-end with a real test client
before the UI was built against it, and the dev server was run against a
live instance of the API with every page (including Members) confirmed
to load without error.

## Notes on the anime lookup

`/anime` calls the free [Jikan API](https://docs.api.jikan.moe/) (no key
needed), caching results locally in `anime_cache` to avoid hammering it.
Every request has a 10s timeout, retries once on a 429 (Jikan rate-limits
at 3 req/sec, 60/min), and any failure — bad status, timeout, DNS/SSL
connection error — turns into a clear message instead of a raw 500. If
search/random/top ever come back empty, the error message returned by the
API now says exactly what failed (network unreachable, rate-limited,
unexpected response shape, etc.) rather than a generic "not found" —
worth checking that message first if it acts up again.

## Leaderboard update notifications

Set `LEADERBOARD_UPDATES_WEBHOOK_URL` in `.env` (create one via a
channel's Settings -> Integrations -> Webhooks -> New Webhook -> Copy
Webhook URL) and that channel gets a short automatic post whenever points
change or a competition resets — whether the change came from a slash
command or the dashboard. A webhook is used (not the bot's own
connection) specifically so the dashboard/API, which has no live Discord
connection, can post the same way the bot does. Leave it blank to disable
entirely. Tested with a mocked webhook: fires the right payload when
configured, silently no-ops when it isn't, and never blocks the
underlying points/reset action even if the webhook post itself fails.

## What could still be improved

- Discord OAuth2's live HTTP calls are untested against real Discord (see above)
- No database migrations (Alembic) — schema changes mean recreating `database/bas.db` for now
- The dashboard's channel dropdowns and member pickers rely on the bot's token and the Server Members intent. If Discord can't be reached, or the intent is off, they fall back to typing the channel/Discord ID by hand (with a message saying why) rather than breaking — but those pickers, and the confirmation dialogs, were verified by type-checking, building, and loading every module through Vite, not by clicking through them in a real browser. Worth a quick manual pass.
- Manually toggling a member's committee status on the Members page is a local override only — it doesn't touch their actual Discord roles, and a future Discord login will still resolve committee status from their real roles, not this override
- CORS and the OAuth2 redirect are hardcoded to `localhost` — update `DASHBOARD_URL`, `OAUTH_REDIRECT_URI`, and the CORS origins in `backend/api/main.py` before hosting anywhere public

Every piece — bot, API, and (through the API) the dashboard — traces back
to the same `backend/services/` functions. No duplicated business logic
anywhere in the stack.

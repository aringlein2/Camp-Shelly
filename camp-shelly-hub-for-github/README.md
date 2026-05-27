# Camp Shelly Hub

A simple, mobile-first, private web hub for a small group going on a camping trip together. Built with Flask + SQLite + Tailwind CDN. No Facebook account, no passwords — just an approved phone-number list.

## What's inside

- Home dashboard with trip info, pinned announcement, latest activity
- Admin-only announcements (with pinning, priority)
- Topic discussion boards with posts, replies, tags, status
- Gear Swap (structured offer/request board)
- Meal Ideas library (with dietary tags, cleanup level)
- Ride Share
- Activities
- FAQ (admin-managed, grouped by category)
- Packing List (static, printable)
- Lost & Found
- Global search across everything
- Admin dashboard: households, people, roles

## Quick start (local)

```bash
git clone <this-repo> camp-shelly-hub
cd camp-shelly-hub
cp .env.example .env
# edit .env — set SECRET_KEY and ADMIN_PHONE to your number
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Open http://localhost:8000 and sign in with the phone number you set in `ADMIN_PHONE`.

## Docker

```bash
cp .env.example .env
# edit .env
docker compose up -d --build
```

The SQLite DB lives in `./data/camp_shelly.db` and is mounted into the container so it survives restarts.

## Adding everyone else

Sign in as admin → **Admin → People → + Add person**. Enter their name, phone, and household. They sign in by entering that same phone number on the access screen.

## Privacy notes

- The site sends `<meta name="robots" content="noindex, nofollow">` and serves `/robots.txt` that disallows everything. Search engines won't index it, but anyone with the URL and an approved phone number can get in.
- Phone numbers are stored normalized (digits only). They're never displayed publicly — admins only see the last 4 digits.
- Avoid posting kids' full names, medical info, or detailed home-empty travel dates. The site shows a reminder in the footer.
- This is **trust-based access** for a small known group. It is not a substitute for a real auth system. Don't reuse it for sensitive data.

## Tech

- Flask 3 + Jinja2 templates
- SQLite (file at `data/camp_shelly.db`)
- Tailwind via CDN (no build step)
- Gunicorn in Docker

## Project layout

```
camp-shelly-hub/
├── app/
│   ├── __init__.py           # app factory, route gate, robots.txt
│   ├── auth.py               # phone-based session auth
│   ├── db.py                 # SQLite helpers
│   ├── schema.sql            # 11 tables
│   ├── seed.py               # creates admin from ADMIN_PHONE on first run
│   ├── utils.py              # phone normalize, categories, tags
│   ├── blueprints/           # one module per section
│   └── templates/            # Jinja2 templates
├── data/                     # SQLite DB lives here (gitignored)
├── requirements.txt
├── run.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Backup

The whole app state is in `data/camp_shelly.db`. Copy that file to back up; restore by putting it back.

```bash
sqlite3 data/camp_shelly.db .dump > backup.sql      # text dump
cp data/camp_shelly.db backup.db                    # binary copy
```

## v1 scope vs later phases

**Built (v1):**
phone access, dashboard, announcements, topic posts+replies, search, gear swap, meal ideas, FAQ, admin dashboard, packing list, ride share, activities, lost & found.

**Deliberately not built yet (kept simple):**
photo uploads, SMS verification, household-specific invite links, CSV export, email digests, push notifications, real-time chat, likes/reactions, full username+password accounts.

These can be added later without major restructuring.

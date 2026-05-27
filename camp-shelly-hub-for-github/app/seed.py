"""Seed the database with the admin user (from env) and a small set of example
FAQ/packing/meal items on first run.
"""
from . import db
from .utils import normalize_phone


PACKING_LIST_HINT = "See the Packing List page."

SEED_FAQ = [
    ("What time does check-in start on Friday?",
     "Check-in opens at 3:00 PM. If you'll arrive earlier or later, post in the General Questions board so people know to watch for you.",
     "Arrival and Check-In"),
    ("Are showers available at the campground?",
     "Yes — there are shared showers near the main bathhouse. Bring shower shoes and a towel.",
     "Bathrooms and Showers"),
    ("Can we have a campfire?",
     "Fires are allowed in designated fire rings unless there's a county burn ban. We'll post any restrictions in Announcements.",
     "Fires and Firewood"),
    ("What's the food plan?",
     "Households cook their own breakfast and lunch. Saturday dinner is a shared group meal — sign up on the Meal Ideas page.",
     "Food"),
    ("Are pets welcome?",
     "Leashed dogs are welcome at this campground. Please clean up and be mindful of kids and other campers.",
     "Pets"),
]


def seed_initial_data(app):
    existing = db.query("SELECT id FROM participants LIMIT 1", one=True)
    if existing:
        return

    admin_phone_raw = app.config.get("ADMIN_PHONE", "")
    admin_phone = normalize_phone(admin_phone_raw)
    if not admin_phone:
        # Fallback so the app still boots; admin will need to add themselves later via DB.
        admin_phone = "5550000000"

    admin_name = app.config.get("ADMIN_NAME", "Admin")
    household_name = app.config.get("ADMIN_HOUSEHOLD", "Admin Household")

    hh_id = db.execute(
        "INSERT INTO households (household_name) VALUES (?)",
        (household_name,),
    )
    db.execute(
        """INSERT INTO participants (household_id, name, display_name, phone_normalized, role, access_enabled)
           VALUES (?, ?, ?, ?, 'admin', 1)""",
        (hh_id, admin_name, admin_name, admin_phone),
    )

    for q, a, cat in SEED_FAQ:
        db.execute(
            "INSERT INTO faq_items (question, answer, category) VALUES (?, ?, ?)",
            (q, a, cat),
        )

    # Welcome announcement
    db.execute(
        """INSERT INTO announcements (title, body, priority, pinned, created_by)
           VALUES (?, ?, 'normal', 1, 1)""",
        (
            "Welcome to Camp Shelly Hub!",
            "Use this site to ask questions, swap gear, share meal ideas, and coordinate rides. "
            "Be kind, keep posts short, and avoid sharing kids' full names or other sensitive info.",
        ),
    )

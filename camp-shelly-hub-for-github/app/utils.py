"""Small helpers used across blueprints."""
import re
import bleach
from datetime import datetime


def normalize_phone(raw):
    """Strip all non-digits. Returns last 10 digits if longer (US-style).

    This is intentionally lightweight — meant for a small trusted group.
    """
    if not raw:
        return ""
    digits = re.sub(r"\D", "", raw)
    if len(digits) > 10:
        digits = digits[-10:]
    return digits


def mask_phone(normalized):
    """Show only last 4 digits, e.g. (***) ***-4567."""
    if not normalized or len(normalized) < 4:
        return "***-****"
    return f"***-***-{normalized[-4:]}"


ALLOWED_TAGS = ["b", "i", "em", "strong", "u", "a", "br", "p", "ul", "ol", "li"]
ALLOWED_ATTRS = {"a": ["href", "title", "rel"]}


def clean_html(text):
    """Sanitize user-submitted text. Allow simple formatting, escape the rest."""
    if not text:
        return ""
    return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)


def nl2br(text):
    """Convert newlines to <br>; assumes text is already sanitized/escaped upstream."""
    if not text:
        return ""
    return text.replace("\n", "<br>\n")


def fmt_dt(value):
    """Pretty-print SQLite timestamp (UTC string) for display."""
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace(" ", "T"))
        return dt.strftime("%b %-d, %Y at %-I:%M %p") if hasattr(dt, "strftime") else value
    except Exception:
        return value


def parse_tags(raw):
    if not raw:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


POST_CATEGORIES = [
    "General Questions",
    "First-Time Campers",
    "Gear Swap",
    "Food & Meals",
    "Ride Share / Caravan",
    "Kids & Youth Activities",
    "Campfire / Music / Games",
    "Accessibility & Comfort",
    "Weather / Packing",
    "Lost & Found",
]

POST_TAGS = [
    "Question", "Answered", "Important", "Offer", "Needed",
    "Meal Idea", "Ride Available", "Ride Needed", "Kid-Friendly",
    "Vegetarian", "Packing", "Resolved",
]

GEAR_CATEGORIES = [
    "Tent", "Sleeping bag", "Sleeping pad", "Camp chair",
    "Lantern/light", "Cooler", "Stove/cooking gear", "Table",
    "Kid gear", "Miscellaneous",
]

MEAL_TYPES = ["Breakfast", "Lunch", "Dinner", "Snack", "Dessert"]

DIETARY_TAGS = [
    "Vegetarian", "Vegan", "Gluten-free", "Dairy-free",
    "Kid-friendly", "No-cook", "Dutch oven", "Make-ahead",
]

CLEANUP_LEVELS = ["Easy", "Moderate", "Regretful"]

FAQ_CATEGORIES = [
    "Arrival and Check-In", "Packing", "Food", "Bathrooms and Showers",
    "Campground Rules", "Fires and Firewood", "Weather", "Kids and Youth",
    "Accessibility", "Gear", "Pets", "Cancellation or Change of Plans",
]

AGE_GROUPS = ["Adults", "Youth", "Kids", "All Ages"]

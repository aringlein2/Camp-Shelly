"""Track which sections a participant has viewed and compute unread counts.

Used to render red badges on the dashboard buttons.
"""
from . import db


SECTIONS = [
    "announcements",
    "posts",
    "gear",
    "meals",
    "rides",
    "activities",
    "faq",
    "lost_found",
]


def mark_viewed(participant_id, section):
    """Record that this participant has just viewed `section`.

    Uses SQLite's CURRENT_TIMESTAMP so the format matches every other
    created_at column ("YYYY-MM-DD HH:MM:SS") — that way string comparison
    against created_at works correctly.
    """
    if not participant_id or section not in SECTIONS:
        return
    db.execute(
        """INSERT INTO section_views (participant_id, section, last_viewed_at)
           VALUES (?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(participant_id, section)
           DO UPDATE SET last_viewed_at = CURRENT_TIMESTAMP""",
        (participant_id, section),
    )


def _last_viewed_map(participant_id):
    rows = db.query(
        "SELECT section, last_viewed_at FROM section_views WHERE participant_id = ?",
        (participant_id,),
    )
    return {r["section"]: r["last_viewed_at"] for r in rows}


def unread_counts(participant_id):
    """Return {section: count_of_new_items_since_last_view, excluding own posts}.

    For 'posts' we count both new posts AND new replies (any activity).
    If a section has never been viewed, EVERYTHING from other people counts.
    """
    if not participant_id:
        return {s: 0 for s in SECTIONS}

    last = _last_viewed_map(participant_id)
    # Far-past sentinel so "never viewed" returns full count.
    # Uses space (not T) to match SQLite CURRENT_TIMESTAMP format.
    epoch = "1970-01-01 00:00:00"

    def since(section):
        return last.get(section, epoch)

    counts = {}

    counts["announcements"] = db.query(
        """SELECT COUNT(*) AS c FROM announcements
           WHERE created_at > ? AND (created_by IS NULL OR created_by != ?)""",
        (since("announcements"), participant_id),
        one=True,
    )["c"]

    posts_view_ts = since("posts")
    new_posts = db.query(
        """SELECT COUNT(*) AS c FROM posts
           WHERE created_at > ? AND (author_id IS NULL OR author_id != ?)""",
        (posts_view_ts, participant_id),
        one=True,
    )["c"]
    new_replies = db.query(
        """SELECT COUNT(*) AS c FROM replies
           WHERE created_at > ? AND (author_id IS NULL OR author_id != ?)""",
        (posts_view_ts, participant_id),
        one=True,
    )["c"]
    counts["posts"] = new_posts + new_replies

    counts["gear"] = db.query(
        """SELECT COUNT(*) AS c FROM gear_items
           WHERE created_at > ? AND (author_id IS NULL OR author_id != ?)""",
        (since("gear"), participant_id), one=True,
    )["c"]

    counts["meals"] = db.query(
        """SELECT COUNT(*) AS c FROM meal_ideas
           WHERE created_at > ? AND (author_id IS NULL OR author_id != ?)""",
        (since("meals"), participant_id), one=True,
    )["c"]

    counts["rides"] = db.query(
        """SELECT COUNT(*) AS c FROM ride_shares
           WHERE created_at > ? AND (author_id IS NULL OR author_id != ?)""",
        (since("rides"), participant_id), one=True,
    )["c"]

    counts["activities"] = db.query(
        """SELECT COUNT(*) AS c FROM activities
           WHERE created_at > ? AND (author_id IS NULL OR author_id != ?)""",
        (since("activities"), participant_id), one=True,
    )["c"]

    counts["lost_found"] = db.query(
        """SELECT COUNT(*) AS c FROM lost_found_items
           WHERE created_at > ? AND (author_id IS NULL OR author_id != ?)""",
        (since("lost_found"), participant_id), one=True,
    )["c"]

    counts["faq"] = db.query(
        "SELECT COUNT(*) AS c FROM faq_items WHERE created_at > ?",
        (since("faq"),), one=True,
    )["c"]

    return counts

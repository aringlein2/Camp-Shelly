from flask import Blueprint, render_template, g
from .. import db
from ..views_tracker import unread_counts

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    pinned = db.query(
        "SELECT * FROM announcements WHERE pinned = 1 ORDER BY created_at DESC LIMIT 1",
        one=True,
    )
    latest_announcements = db.query(
        "SELECT * FROM announcements ORDER BY pinned DESC, created_at DESC LIMIT 3"
    )
    latest_posts = db.query(
        """SELECT p.*, pa.display_name AS author_name
           FROM posts p LEFT JOIN participants pa ON pa.id = p.author_id
           ORDER BY p.created_at DESC LIMIT 5"""
    )
    badges = unread_counts(g.user["id"]) if g.get("user") else {}
    return render_template(
        "dashboard.html",
        pinned=pinned,
        latest_announcements=latest_announcements,
        latest_posts=latest_posts,
        badges=badges,
    )

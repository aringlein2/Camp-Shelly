from flask import Blueprint, render_template, request
from .. import db

bp = Blueprint("search", __name__, url_prefix="/search")


@bp.route("/")
def index():
    q = request.args.get("q", "").strip()
    results = {"posts": [], "replies": [], "gear": [], "meals": [], "rides": [],
               "activities": [], "faq": [], "lost_found": [], "announcements": []}
    if q:
        like = f"%{q}%"
        results["posts"] = db.query(
            """SELECT id, title, category, body FROM posts
               WHERE title LIKE ? OR body LIKE ? ORDER BY created_at DESC LIMIT 25""",
            (like, like),
        )
        results["replies"] = db.query(
            """SELECT r.id, r.post_id, r.body, p.title AS post_title
               FROM replies r JOIN posts p ON p.id = r.post_id
               WHERE r.body LIKE ? ORDER BY r.created_at DESC LIMIT 25""",
            (like,),
        )
        results["gear"] = db.query(
            """SELECT id, item_name, description, type, status FROM gear_items
               WHERE item_name LIKE ? OR description LIKE ? ORDER BY created_at DESC LIMIT 25""",
            (like, like),
        )
        results["meals"] = db.query(
            """SELECT id, title, description, meal_type FROM meal_ideas
               WHERE title LIKE ? OR description LIKE ? OR cooking_instructions LIKE ?
               ORDER BY created_at DESC LIMIT 25""",
            (like, like, like),
        )
        results["rides"] = db.query(
            """SELECT id, leaving_from, notes, type FROM ride_shares
               WHERE leaving_from LIKE ? OR notes LIKE ?
               ORDER BY created_at DESC LIMIT 25""",
            (like, like),
        )
        results["activities"] = db.query(
            """SELECT id, title, description FROM activities
               WHERE title LIKE ? OR description LIKE ?
               ORDER BY created_at DESC LIMIT 25""",
            (like, like),
        )
        results["faq"] = db.query(
            """SELECT id, question, answer, category FROM faq_items
               WHERE question LIKE ? OR answer LIKE ?
               ORDER BY category LIMIT 25""",
            (like, like),
        )
        results["lost_found"] = db.query(
            """SELECT id, description, type, status FROM lost_found_items
               WHERE description LIKE ? ORDER BY created_at DESC LIMIT 25""",
            (like,),
        )
        results["announcements"] = db.query(
            """SELECT id, title, body FROM announcements
               WHERE title LIKE ? OR body LIKE ? ORDER BY created_at DESC LIMIT 25""",
            (like, like),
        )
    total = sum(len(v) for v in results.values())
    return render_template("search.html", q=q, results=results, total=total)

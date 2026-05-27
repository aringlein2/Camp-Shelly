from flask import Blueprint, render_template, request, redirect, url_for, g, abort
from .. import db
from ..views_tracker import mark_viewed

bp = Blueprint("lost_found", __name__, url_prefix="/lost-found")
STATUSES = ["open", "claimed", "resolved"]


def _can_edit(item, user):
    return user["role"] == "admin" or item["author_id"] == user["id"]


@bp.route("/")
def index():
    t = request.args.get("type", "")
    sql = """SELECT l.*, p.display_name AS author_name
             FROM lost_found_items l LEFT JOIN participants p ON p.id = l.author_id WHERE 1=1"""
    args = []
    if t in ("found", "missing"):
        sql += " AND l.type = ?"
        args.append(t)
    sql += " ORDER BY l.status = 'resolved', l.created_at DESC"
    items = db.query(sql, tuple(args))
    if g.get("user"):
        mark_viewed(g.user["id"], "lost_found")
    return render_template("lost_found/index.html", items=items, type_filter=t)


@bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        t = request.form.get("type", "")
        if t not in ("found", "missing"):
            return redirect(url_for("lost_found.new"))
        db.execute(
            """INSERT INTO lost_found_items (type, description, contact_preference, author_id)
               VALUES (?, ?, ?, ?)""",
            (t, request.form.get("description", "").strip(),
             request.form.get("contact_preference", "").strip(), g.user["id"]),
        )
        return redirect(url_for("lost_found.index"))
    return render_template("lost_found/edit.html", item=None, statuses=STATUSES)


@bp.route("/<int:item_id>/edit", methods=["GET", "POST"])
def edit(item_id):
    item = db.query("SELECT * FROM lost_found_items WHERE id = ?", (item_id,), one=True)
    if not item:
        abort(404)
    if not _can_edit(item, g.user):
        abort(403)
    if request.method == "POST":
        db.execute(
            """UPDATE lost_found_items SET type=?, description=?, contact_preference=?,
               status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?""",
            (request.form.get("type", item["type"]),
             request.form.get("description", "").strip(),
             request.form.get("contact_preference", "").strip(),
             request.form.get("status", item["status"]), item_id),
        )
        return redirect(url_for("lost_found.index"))
    return render_template("lost_found/edit.html", item=item, statuses=STATUSES)


@bp.route("/<int:item_id>/delete", methods=["POST"])
def delete(item_id):
    item = db.query("SELECT * FROM lost_found_items WHERE id = ?", (item_id,), one=True)
    if not item:
        abort(404)
    if not _can_edit(item, g.user):
        abort(403)
    db.execute("DELETE FROM lost_found_items WHERE id = ?", (item_id,))
    return redirect(url_for("lost_found.index"))

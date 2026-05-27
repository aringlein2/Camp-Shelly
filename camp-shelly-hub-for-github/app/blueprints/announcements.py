from flask import Blueprint, render_template, request, redirect, url_for, g, flash, abort
from .. import db
from ..auth import admin_required
from ..views_tracker import mark_viewed

bp = Blueprint("announcements", __name__, url_prefix="/announcements")

PRIORITIES = ["normal", "important", "urgent"]


@bp.route("/")
def index():
    items = db.query(
        """SELECT a.*, p.display_name AS author_name
           FROM announcements a LEFT JOIN participants p ON p.id = a.created_by
           ORDER BY a.pinned DESC, a.created_at DESC"""
    )
    if g.get("user"):
        mark_viewed(g.user["id"], "announcements")
    return render_template("announcements/index.html", items=items)


@bp.route("/new", methods=["GET", "POST"])
@admin_required
def new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        priority = request.form.get("priority", "normal")
        pinned = 1 if request.form.get("pinned") else 0
        if not title or not body:
            flash("Title and body are required.", "error")
            return render_template("announcements/edit.html", item=None, priorities=PRIORITIES)
        db.execute(
            """INSERT INTO announcements (title, body, priority, pinned, created_by)
               VALUES (?, ?, ?, ?, ?)""",
            (title, body, priority, pinned, g.user["id"]),
        )
        flash("Announcement posted.", "success")
        return redirect(url_for("announcements.index"))
    return render_template("announcements/edit.html", item=None, priorities=PRIORITIES)


@bp.route("/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def edit(item_id):
    item = db.query("SELECT * FROM announcements WHERE id = ?", (item_id,), one=True)
    if not item:
        abort(404)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        priority = request.form.get("priority", "normal")
        pinned = 1 if request.form.get("pinned") else 0
        db.execute(
            """UPDATE announcements SET title=?, body=?, priority=?, pinned=?, updated_at=CURRENT_TIMESTAMP
               WHERE id=?""",
            (title, body, priority, pinned, item_id),
        )
        flash("Announcement updated.", "success")
        return redirect(url_for("announcements.index"))
    return render_template("announcements/edit.html", item=item, priorities=PRIORITIES)


@bp.route("/<int:item_id>/delete", methods=["POST"])
@admin_required
def delete(item_id):
    db.execute("DELETE FROM announcements WHERE id = ?", (item_id,))
    flash("Announcement deleted.", "success")
    return redirect(url_for("announcements.index"))

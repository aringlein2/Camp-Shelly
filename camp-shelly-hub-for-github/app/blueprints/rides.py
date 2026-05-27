from flask import Blueprint, render_template, request, redirect, url_for, g, flash, abort
from .. import db
from ..views_tracker import mark_viewed

bp = Blueprint("rides", __name__, url_prefix="/rides")
STATUSES = ["open", "filled", "resolved"]


def _can_edit(item, user):
    return user["role"] == "admin" or item["author_id"] == user["id"]


@bp.route("/")
def index():
    t = request.args.get("type", "")
    sql = """SELECT r.*, p.display_name AS author_name
             FROM ride_shares r LEFT JOIN participants p ON p.id = r.author_id WHERE 1=1"""
    args = []
    if t in ("offering", "looking"):
        sql += " AND r.type = ?"
        args.append(t)
    sql += " ORDER BY r.status = 'resolved', r.departure_datetime IS NULL, r.departure_datetime ASC, r.created_at DESC"
    items = db.query(sql, tuple(args))
    if g.get("user"):
        mark_viewed(g.user["id"], "rides")
    return render_template("rides/index.html", items=items, type_filter=t)


@bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        d = _form()
        if d["type"] not in ("offering", "looking"):
            flash("Please choose offering or looking.", "error")
            return render_template("rides/edit.html", item=None, statuses=STATUSES)
        db.execute(
            """INSERT INTO ride_shares (type, leaving_from, departure_datetime, return_datetime,
                seats_available, gear_space, contact_preference, notes, author_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (d["type"], d["leaving_from"], d["departure_datetime"], d["return_datetime"],
             d["seats_available"], d["gear_space"], d["contact_preference"], d["notes"], g.user["id"]),
        )
        return redirect(url_for("rides.index"))
    return render_template("rides/edit.html", item=None, statuses=STATUSES)


@bp.route("/<int:item_id>/edit", methods=["GET", "POST"])
def edit(item_id):
    item = db.query("SELECT * FROM ride_shares WHERE id = ?", (item_id,), one=True)
    if not item:
        abort(404)
    if not _can_edit(item, g.user):
        abort(403)
    if request.method == "POST":
        d = _form()
        status = request.form.get("status", item["status"])
        db.execute(
            """UPDATE ride_shares SET type=?, leaving_from=?, departure_datetime=?, return_datetime=?,
                seats_available=?, gear_space=?, contact_preference=?, notes=?, status=?,
                updated_at=CURRENT_TIMESTAMP WHERE id=?""",
            (d["type"], d["leaving_from"], d["departure_datetime"], d["return_datetime"],
             d["seats_available"], d["gear_space"], d["contact_preference"], d["notes"], status, item_id),
        )
        return redirect(url_for("rides.index"))
    return render_template("rides/edit.html", item=item, statuses=STATUSES)


@bp.route("/<int:item_id>/delete", methods=["POST"])
def delete(item_id):
    item = db.query("SELECT * FROM ride_shares WHERE id = ?", (item_id,), one=True)
    if not item:
        abort(404)
    if not _can_edit(item, g.user):
        abort(403)
    db.execute("DELETE FROM ride_shares WHERE id = ?", (item_id,))
    return redirect(url_for("rides.index"))


def _form():
    f = request.form
    return {
        "type": f.get("type", ""),
        "leaving_from": f.get("leaving_from", "").strip(),
        "departure_datetime": f.get("departure_datetime", "").strip(),
        "return_datetime": f.get("return_datetime", "").strip(),
        "seats_available": f.get("seats_available", "").strip(),
        "gear_space": f.get("gear_space", "").strip(),
        "contact_preference": f.get("contact_preference", "").strip(),
        "notes": f.get("notes", "").strip(),
    }

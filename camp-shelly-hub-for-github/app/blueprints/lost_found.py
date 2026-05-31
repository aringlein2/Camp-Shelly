from flask import Blueprint, render_template, request, redirect, url_for, g, flash, abort, current_app
from .. import db
from ..views_tracker import mark_viewed
from ..images import save_resized, delete_image

bp = Blueprint("lost_found", __name__, url_prefix="/lost-found")
STATUSES = ["open", "claimed", "resolved"]


def _can_edit(item, user):
    return user["role"] == "admin" or item["author_id"] == user["id"]


def _form_photo(existing=None):
    photo = request.files.get("photo")
    try:
        new_img = save_resized(photo, current_app.config["UPLOAD_DIR"])
    except ValueError as e:
        return existing, str(e)
    if new_img:
        if existing:
            delete_image(existing, current_app.config["UPLOAD_DIR"])
        return new_img, None
    return existing, None


@bp.route("/")
def index():
    t = request.args.get("type", "")
    sql = """SELECT l.*, p.display_name AS author_name
             FROM lost_found_items l LEFT JOIN participants p ON p.id = l.author_id WHERE 1=1"""
    args = []
    if t in ("found", "missing"):
        sql += " AND l.type = ?"; args.append(t)
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
        photo_url, err = _form_photo(None)
        if err:
            flash(err, "error")
            return render_template("lost_found/edit.html", item=None, statuses=STATUSES)
        db.execute(
            """INSERT INTO lost_found_items (type, description, contact_preference, photo_url, author_id)
               VALUES (?, ?, ?, ?, ?)""",
            (t, request.form.get("description", "").strip(),
             request.form.get("contact_preference", "").strip(),
             photo_url, g.user["id"]),
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
        photo_url, err = _form_photo(item["photo_url"])
        if err:
            flash(err, "error")
            return render_template("lost_found/edit.html", item=item, statuses=STATUSES)
        if request.form.get("remove_photo") and photo_url:
            delete_image(photo_url, current_app.config["UPLOAD_DIR"])
            photo_url = None
        db.execute(
            """UPDATE lost_found_items SET type=?, description=?, contact_preference=?,
               status=?, photo_url=?, updated_at=CURRENT_TIMESTAMP WHERE id=?""",
            (request.form.get("type", item["type"]),
             request.form.get("description", "").strip(),
             request.form.get("contact_preference", "").strip(),
             request.form.get("status", item["status"]),
             photo_url, item_id),
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
    if item["photo_url"]:
        delete_image(item["photo_url"], current_app.config["UPLOAD_DIR"])
    db.execute("DELETE FROM lost_found_items WHERE id = ?", (item_id,))
    return redirect(url_for("lost_found.index"))

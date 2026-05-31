from flask import Blueprint, render_template, request, redirect, url_for, g, flash, abort, current_app
from .. import db
from ..utils import GEAR_CATEGORIES
from ..views_tracker import mark_viewed
from ..images import save_resized, delete_image

bp = Blueprint("gear", __name__, url_prefix="/gear")

STATUSES = ["available", "claimed", "still_needed", "resolved"]
STATUS_LABELS = {"available": "Available", "claimed": "Claimed",
                 "still_needed": "Still needed", "resolved": "Resolved"}


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
    type_filter = request.args.get("type", "")
    cat = request.args.get("category", "")
    q = request.args.get("q", "").strip()
    sql = """SELECT g.*, p.display_name AS author_name
             FROM gear_items g LEFT JOIN participants p ON p.id = g.author_id WHERE 1=1"""
    args = []
    if type_filter in ("offering", "looking"):
        sql += " AND g.type = ?"; args.append(type_filter)
    if cat:
        sql += " AND g.category = ?"; args.append(cat)
    if q:
        sql += " AND (g.item_name LIKE ? OR g.description LIKE ?)"
        args += [f"%{q}%", f"%{q}%"]
    sql += " ORDER BY g.status = 'resolved', g.created_at DESC"
    items = db.query(sql, tuple(args))
    if g.get("user"):
        mark_viewed(g.user["id"], "gear")
    return render_template("gear/index.html", items=items, categories=GEAR_CATEGORIES,
                           status_labels=STATUS_LABELS, type_filter=type_filter, cat=cat, q=q)


@bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        data = _form()
        if not data["item_name"] or data["type"] not in ("offering", "looking"):
            flash("Item name and type are required.", "error")
            return render_template("gear/edit.html", item=None, categories=GEAR_CATEGORIES, statuses=STATUSES)
        image_path, err = _form_photo(None)
        if err:
            flash(err, "error")
            return render_template("gear/edit.html", item=None, categories=GEAR_CATEGORIES, statuses=STATUSES)
        default_status = "available" if data["type"] == "offering" else "still_needed"
        db.execute(
            """INSERT INTO gear_items (type, item_name, category, quantity, description,
                pickup_return_notes, contact_preference, status, author_id, image_path)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data["type"], data["item_name"], data["category"], data["quantity"],
             data["description"], data["pickup_return_notes"], data["contact_preference"],
             default_status, g.user["id"], image_path),
        )
        flash("Gear item added.", "success")
        return redirect(url_for("gear.index"))
    return render_template("gear/edit.html", item=None, categories=GEAR_CATEGORIES, statuses=STATUSES)


@bp.route("/<int:item_id>/edit", methods=["GET", "POST"])
def edit(item_id):
    item = db.query("SELECT * FROM gear_items WHERE id = ?", (item_id,), one=True)
    if not item:
        abort(404)
    if not _can_edit(item, g.user):
        abort(403)
    if request.method == "POST":
        data = _form()
        status = request.form.get("status", item["status"])
        image_path, err = _form_photo(item["image_path"])
        if err:
            flash(err, "error")
            return render_template("gear/edit.html", item=item, categories=GEAR_CATEGORIES, statuses=STATUSES)
        if request.form.get("remove_photo") and image_path:
            delete_image(image_path, current_app.config["UPLOAD_DIR"])
            image_path = None
        db.execute(
            """UPDATE gear_items SET type=?, item_name=?, category=?, quantity=?, description=?,
                pickup_return_notes=?, contact_preference=?, status=?, image_path=?, updated_at=CURRENT_TIMESTAMP
               WHERE id=?""",
            (data["type"], data["item_name"], data["category"], data["quantity"],
             data["description"], data["pickup_return_notes"], data["contact_preference"],
             status, image_path, item_id),
        )
        flash("Gear item updated.", "success")
        return redirect(url_for("gear.index"))
    return render_template("gear/edit.html", item=item, categories=GEAR_CATEGORIES, statuses=STATUSES)


@bp.route("/<int:item_id>/delete", methods=["POST"])
def delete(item_id):
    item = db.query("SELECT * FROM gear_items WHERE id = ?", (item_id,), one=True)
    if not item:
        abort(404)
    if not _can_edit(item, g.user):
        abort(403)
    if item["image_path"]:
        delete_image(item["image_path"], current_app.config["UPLOAD_DIR"])
    db.execute("DELETE FROM gear_items WHERE id = ?", (item_id,))
    return redirect(url_for("gear.index"))


@bp.route("/<int:item_id>/status", methods=["POST"])
def set_status(item_id):
    item = db.query("SELECT * FROM gear_items WHERE id = ?", (item_id,), one=True)
    if not item:
        abort(404)
    if not _can_edit(item, g.user):
        abort(403)
    status = request.form.get("status", "available")
    if status not in STATUSES:
        abort(400)
    db.execute("UPDATE gear_items SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
               (status, item_id))
    return redirect(url_for("gear.index"))


def _form():
    f = request.form
    return {
        "type": f.get("type", ""),
        "item_name": f.get("item_name", "").strip(),
        "category": f.get("category", "").strip(),
        "quantity": f.get("quantity", "").strip(),
        "description": f.get("description", "").strip(),
        "pickup_return_notes": f.get("pickup_return_notes", "").strip(),
        "contact_preference": f.get("contact_preference", "").strip(),
    }

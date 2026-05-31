from flask import Blueprint, render_template, request, redirect, url_for, g, flash, abort, current_app
from .. import db
from ..utils import AGE_GROUPS
from ..views_tracker import mark_viewed
from ..images import save_resized, delete_image

bp = Blueprint("activities", __name__, url_prefix="/activities")


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
    age = request.args.get("age", "")
    sql = """SELECT a.*, p.display_name AS author_name
             FROM activities a LEFT JOIN participants p ON p.id = a.author_id WHERE 1=1"""
    args = []
    if age:
        sql += " AND a.age_group = ?"; args.append(age)
    sql += " ORDER BY a.created_at DESC"
    items = db.query(sql, tuple(args))
    if g.get("user"):
        mark_viewed(g.user["id"], "activities")
    return render_template("activities/index.html", items=items, age_groups=AGE_GROUPS, age=age)


@bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        d = _form()
        image_path, err = _form_photo(None)
        if err:
            flash(err, "error")
            return render_template("activities/edit.html", item=None, age_groups=AGE_GROUPS)
        db.execute(
            """INSERT INTO activities (title, description, age_group, supplies_needed,
                willing_to_lead, preferred_time, notes, author_id, image_path)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (d["title"], d["description"], d["age_group"], d["supplies_needed"],
             d["willing_to_lead"], d["preferred_time"], d["notes"], g.user["id"], image_path),
        )
        return redirect(url_for("activities.index"))
    return render_template("activities/edit.html", item=None, age_groups=AGE_GROUPS)


@bp.route("/<int:item_id>/edit", methods=["GET", "POST"])
def edit(item_id):
    item = db.query("SELECT * FROM activities WHERE id = ?", (item_id,), one=True)
    if not item:
        abort(404)
    if not _can_edit(item, g.user):
        abort(403)
    if request.method == "POST":
        d = _form()
        image_path, err = _form_photo(item["image_path"])
        if err:
            flash(err, "error")
            return render_template("activities/edit.html", item=item, age_groups=AGE_GROUPS)
        if request.form.get("remove_photo") and image_path:
            delete_image(image_path, current_app.config["UPLOAD_DIR"])
            image_path = None
        db.execute(
            """UPDATE activities SET title=?, description=?, age_group=?, supplies_needed=?,
               willing_to_lead=?, preferred_time=?, notes=?, image_path=?, updated_at=CURRENT_TIMESTAMP WHERE id=?""",
            (d["title"], d["description"], d["age_group"], d["supplies_needed"],
             d["willing_to_lead"], d["preferred_time"], d["notes"], image_path, item_id),
        )
        return redirect(url_for("activities.index"))
    return render_template("activities/edit.html", item=item, age_groups=AGE_GROUPS)


@bp.route("/<int:item_id>/delete", methods=["POST"])
def delete(item_id):
    item = db.query("SELECT * FROM activities WHERE id = ?", (item_id,), one=True)
    if not item:
        abort(404)
    if not _can_edit(item, g.user):
        abort(403)
    if item["image_path"]:
        delete_image(item["image_path"], current_app.config["UPLOAD_DIR"])
    db.execute("DELETE FROM activities WHERE id = ?", (item_id,))
    return redirect(url_for("activities.index"))


def _form():
    f = request.form
    return {
        "title": f.get("title", "").strip(),
        "description": f.get("description", "").strip(),
        "age_group": f.get("age_group", "").strip(),
        "supplies_needed": f.get("supplies_needed", "").strip(),
        "willing_to_lead": 1 if f.get("willing_to_lead") else 0,
        "preferred_time": f.get("preferred_time", "").strip(),
        "notes": f.get("notes", "").strip(),
    }

from flask import Blueprint, render_template, request, redirect, url_for, g, flash, abort
from .. import db
from ..utils import MEAL_TYPES, DIETARY_TAGS, CLEANUP_LEVELS
from ..views_tracker import mark_viewed

bp = Blueprint("meals", __name__, url_prefix="/meals")


def _can_edit(item, user):
    return user["role"] == "admin" or item["author_id"] == user["id"]


@bp.route("/")
def index():
    meal_type = request.args.get("meal_type", "")
    diet = request.args.get("diet", "")
    cleanup = request.args.get("cleanup", "")
    q = request.args.get("q", "").strip()
    sql = """SELECT m.*, p.display_name AS author_name
             FROM meal_ideas m LEFT JOIN participants p ON p.id = m.author_id
             WHERE 1=1"""
    args = []
    if meal_type:
        sql += " AND m.meal_type = ?"
        args.append(meal_type)
    if diet:
        sql += " AND m.dietary_tags LIKE ?"
        args.append(f"%{diet}%")
    if cleanup:
        sql += " AND m.cleanup_level = ?"
        args.append(cleanup)
    if q:
        sql += " AND (m.title LIKE ? OR m.description LIKE ?)"
        args += [f"%{q}%", f"%{q}%"]
    sql += " ORDER BY m.created_at DESC"
    items = db.query(sql, tuple(args))
    if g.get("user"):
        mark_viewed(g.user["id"], "meals")
    return render_template(
        "meals/index.html",
        items=items,
        meal_types=MEAL_TYPES, dietary_tags=DIETARY_TAGS, cleanup_levels=CLEANUP_LEVELS,
        meal_type=meal_type, diet=diet, cleanup=cleanup, q=q,
    )


@bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        data = _form()
        if not data["title"] or data["meal_type"] not in MEAL_TYPES:
            flash("Meal name and type are required.", "error")
            return render_template("meals/edit.html", item=None,
                                   meal_types=MEAL_TYPES, dietary_tags=DIETARY_TAGS,
                                   cleanup_levels=CLEANUP_LEVELS, selected_diets=data["dietary"])
        db.execute(
            """INSERT INTO meal_ideas (title, meal_type, serves, description, prep_ahead_notes,
                cooking_instructions, equipment_needed, dietary_tags, cleanup_level, author_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data["title"], data["meal_type"], data["serves"], data["description"],
             data["prep_ahead_notes"], data["cooking_instructions"], data["equipment_needed"],
             ",".join(data["dietary"]), data["cleanup_level"], g.user["id"]),
        )
        flash("Meal idea added.", "success")
        return redirect(url_for("meals.index"))
    return render_template("meals/edit.html", item=None,
                           meal_types=MEAL_TYPES, dietary_tags=DIETARY_TAGS,
                           cleanup_levels=CLEANUP_LEVELS, selected_diets=[])


@bp.route("/<int:item_id>")
def detail(item_id):
    item = db.query("""SELECT m.*, p.display_name AS author_name
                       FROM meal_ideas m LEFT JOIN participants p ON p.id = m.author_id
                       WHERE m.id = ?""", (item_id,), one=True)
    if not item:
        abort(404)
    return render_template("meals/detail.html", item=item)


@bp.route("/<int:item_id>/edit", methods=["GET", "POST"])
def edit(item_id):
    item = db.query("SELECT * FROM meal_ideas WHERE id = ?", (item_id,), one=True)
    if not item:
        abort(404)
    if not _can_edit(item, g.user):
        abort(403)
    if request.method == "POST":
        data = _form()
        db.execute(
            """UPDATE meal_ideas SET title=?, meal_type=?, serves=?, description=?,
               prep_ahead_notes=?, cooking_instructions=?, equipment_needed=?,
               dietary_tags=?, cleanup_level=?, updated_at=CURRENT_TIMESTAMP WHERE id=?""",
            (data["title"], data["meal_type"], data["serves"], data["description"],
             data["prep_ahead_notes"], data["cooking_instructions"], data["equipment_needed"],
             ",".join(data["dietary"]), data["cleanup_level"], item_id),
        )
        return redirect(url_for("meals.detail", item_id=item_id))
    selected = item["dietary_tags"].split(",") if item["dietary_tags"] else []
    return render_template("meals/edit.html", item=item,
                           meal_types=MEAL_TYPES, dietary_tags=DIETARY_TAGS,
                           cleanup_levels=CLEANUP_LEVELS, selected_diets=selected)


@bp.route("/<int:item_id>/delete", methods=["POST"])
def delete(item_id):
    item = db.query("SELECT * FROM meal_ideas WHERE id = ?", (item_id,), one=True)
    if not item:
        abort(404)
    if not _can_edit(item, g.user):
        abort(403)
    db.execute("DELETE FROM meal_ideas WHERE id = ?", (item_id,))
    return redirect(url_for("meals.index"))


def _form():
    f = request.form
    return {
        "title": f.get("title", "").strip(),
        "meal_type": f.get("meal_type", "").strip(),
        "serves": f.get("serves", "").strip(),
        "description": f.get("description", "").strip(),
        "prep_ahead_notes": f.get("prep_ahead_notes", "").strip(),
        "cooking_instructions": f.get("cooking_instructions", "").strip(),
        "equipment_needed": f.get("equipment_needed", "").strip(),
        "dietary": f.getlist("dietary"),
        "cleanup_level": f.get("cleanup_level", "").strip(),
    }

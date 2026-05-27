from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, g
from .. import db
from ..auth import admin_required
from ..utils import FAQ_CATEGORIES
from ..views_tracker import mark_viewed

bp = Blueprint("faq", __name__, url_prefix="/faq")


@bp.route("/")
def index():
    items = db.query("SELECT * FROM faq_items ORDER BY category, created_at")
    by_cat = {}
    for it in items:
        by_cat.setdefault(it["category"], []).append(it)
    ordered = [(c, by_cat[c]) for c in FAQ_CATEGORIES if c in by_cat]
    for c, lst in by_cat.items():
        if c not in FAQ_CATEGORIES:
            ordered.append((c, lst))
    if g.get("user"):
        mark_viewed(g.user["id"], "faq")
    return render_template("faq/index.html", grouped=ordered)


@bp.route("/new", methods=["GET", "POST"])
@admin_required
def new():
    if request.method == "POST":
        q = request.form.get("question", "").strip()
        a = request.form.get("answer", "").strip()
        c = request.form.get("category", "").strip()
        if not q or not a or not c:
            flash("Question, answer, and category are required.", "error")
            return render_template("faq/edit.html", item=None, categories=FAQ_CATEGORIES)
        db.execute(
            "INSERT INTO faq_items (question, answer, category) VALUES (?, ?, ?)",
            (q, a, c),
        )
        flash("FAQ item added.", "success")
        return redirect(url_for("faq.index"))
    return render_template("faq/edit.html", item=None, categories=FAQ_CATEGORIES)


@bp.route("/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def edit(item_id):
    item = db.query("SELECT * FROM faq_items WHERE id = ?", (item_id,), one=True)
    if not item:
        abort(404)
    if request.method == "POST":
        db.execute(
            """UPDATE faq_items SET question=?, answer=?, category=?, updated_at=CURRENT_TIMESTAMP
               WHERE id=?""",
            (request.form.get("question", "").strip(),
             request.form.get("answer", "").strip(),
             request.form.get("category", "").strip(),
             item_id),
        )
        return redirect(url_for("faq.index"))
    return render_template("faq/edit.html", item=item, categories=FAQ_CATEGORIES)


@bp.route("/<int:item_id>/delete", methods=["POST"])
@admin_required
def delete(item_id):
    db.execute("DELETE FROM faq_items WHERE id = ?", (item_id,))
    return redirect(url_for("faq.index"))

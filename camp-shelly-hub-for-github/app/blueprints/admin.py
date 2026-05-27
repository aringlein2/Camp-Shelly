from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from .. import db
from ..auth import admin_required
from ..utils import normalize_phone, mask_phone

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
@admin_required
def index():
    counts = {
        "participants": db.query("SELECT COUNT(*) AS c FROM participants", one=True)["c"],
        "households": db.query("SELECT COUNT(*) AS c FROM households", one=True)["c"],
        "posts": db.query("SELECT COUNT(*) AS c FROM posts", one=True)["c"],
        "gear": db.query("SELECT COUNT(*) AS c FROM gear_items", one=True)["c"],
        "meals": db.query("SELECT COUNT(*) AS c FROM meal_ideas", one=True)["c"],
        "rides": db.query("SELECT COUNT(*) AS c FROM ride_shares", one=True)["c"],
        "faq": db.query("SELECT COUNT(*) AS c FROM faq_items", one=True)["c"],
    }
    return render_template("admin/index.html", counts=counts)


# ---------------- Households ----------------

@bp.route("/households")
@admin_required
def households():
    items = db.query(
        """SELECT h.*,
                  (SELECT COUNT(*) FROM participants p WHERE p.household_id = h.id) AS member_count
           FROM households h ORDER BY h.household_name"""
    )
    return render_template("admin/households.html", items=items)


@bp.route("/households/new", methods=["GET", "POST"])
@admin_required
def household_new():
    if request.method == "POST":
        name = request.form.get("household_name", "").strip()
        notes = request.form.get("notes", "").strip()
        if not name:
            flash("Name required.", "error")
            return render_template("admin/household_edit.html", item=None)
        db.execute("INSERT INTO households (household_name, notes) VALUES (?, ?)", (name, notes))
        return redirect(url_for("admin.households"))
    return render_template("admin/household_edit.html", item=None)


@bp.route("/households/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def household_edit(item_id):
    item = db.query("SELECT * FROM households WHERE id = ?", (item_id,), one=True)
    if not item:
        abort(404)
    if request.method == "POST":
        db.execute(
            "UPDATE households SET household_name=?, notes=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (request.form.get("household_name", "").strip(),
             request.form.get("notes", "").strip(), item_id),
        )
        return redirect(url_for("admin.households"))
    return render_template("admin/household_edit.html", item=item)


@bp.route("/households/<int:item_id>/delete", methods=["POST"])
@admin_required
def household_delete(item_id):
    db.execute("DELETE FROM households WHERE id = ?", (item_id,))
    return redirect(url_for("admin.households"))


# ---------------- Participants ----------------

@bp.route("/participants")
@admin_required
def participants():
    items = db.query(
        """SELECT p.*, h.household_name FROM participants p
           LEFT JOIN households h ON h.id = p.household_id
           ORDER BY h.household_name, p.display_name"""
    )
    # Attach masked phone for display
    items = [dict(p) for p in items]
    for p in items:
        p["phone_masked"] = mask_phone(p["phone_normalized"])
    return render_template("admin/participants.html", items=items)


@bp.route("/participants/new", methods=["GET", "POST"])
@admin_required
def participant_new():
    households = db.query("SELECT * FROM households ORDER BY household_name")
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        display = request.form.get("display_name", "").strip() or name
        phone = normalize_phone(request.form.get("phone", ""))
        household_id = request.form.get("household_id") or None
        role = request.form.get("role", "participant")
        access = 1 if request.form.get("access_enabled") else 1  # default on
        if not name or not phone:
            flash("Name and phone are required.", "error")
            return render_template("admin/participant_edit.html", item=None, households=households)
        existing = db.query("SELECT id FROM participants WHERE phone_normalized=?", (phone,), one=True)
        if existing:
            flash("That phone is already in the list.", "error")
            return render_template("admin/participant_edit.html", item=None, households=households)
        db.execute(
            """INSERT INTO participants (household_id, name, display_name, phone_normalized, role, access_enabled)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (household_id, name, display, phone, role, access),
        )
        return redirect(url_for("admin.participants"))
    return render_template("admin/participant_edit.html", item=None, households=households)


@bp.route("/participants/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def participant_edit(item_id):
    item = db.query("SELECT * FROM participants WHERE id = ?", (item_id,), one=True)
    if not item:
        abort(404)
    households = db.query("SELECT * FROM households ORDER BY household_name")
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        display = request.form.get("display_name", "").strip() or name
        phone_raw = request.form.get("phone", "")
        phone = normalize_phone(phone_raw) if phone_raw else item["phone_normalized"]
        household_id = request.form.get("household_id") or None
        role = request.form.get("role", "participant")
        access = 1 if request.form.get("access_enabled") else 0
        db.execute(
            """UPDATE participants SET household_id=?, name=?, display_name=?, phone_normalized=?,
               role=?, access_enabled=?, updated_at=CURRENT_TIMESTAMP WHERE id=?""",
            (household_id, name, display, phone, role, access, item_id),
        )
        return redirect(url_for("admin.participants"))
    item = dict(item)
    item["phone_masked"] = mask_phone(item["phone_normalized"])
    return render_template("admin/participant_edit.html", item=item, households=households)


@bp.route("/participants/<int:item_id>/delete", methods=["POST"])
@admin_required
def participant_delete(item_id):
    db.execute("DELETE FROM participants WHERE id = ?", (item_id,))
    return redirect(url_for("admin.participants"))

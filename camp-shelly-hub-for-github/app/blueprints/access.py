"""Phone-number access gate."""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from .. import db
from ..auth import login_participant, logout
from ..utils import normalize_phone

bp = Blueprint("access", __name__)


@bp.route("/access", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = normalize_phone(request.form.get("phone", ""))
        if not phone:
            flash("Please enter your phone number.", "error")
            return render_template("access.html")
        row = db.query(
            "SELECT * FROM participants WHERE phone_normalized = ? AND access_enabled = 1",
            (phone,),
            one=True,
        )
        if not row:
            flash(
                "That phone number isn't on our list yet. "
                "Reach out to a camp organizer so they can add you.",
                "error",
            )
            return render_template("access.html")
        login_participant(row["id"])
        db.execute(
            "UPDATE participants SET last_access_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(timespec="seconds"), row["id"]),
        )
        return redirect(url_for("dashboard.index"))
    return render_template("access.html")


@bp.route("/logout")
def do_logout():
    logout()
    return redirect(url_for("access.login"))

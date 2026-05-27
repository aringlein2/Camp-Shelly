"""Phone-based session auth."""
from functools import wraps
from flask import session, redirect, url_for, g, flash, abort
from . import db


def login_participant(participant_id):
    session.clear()
    session["pid"] = participant_id
    session.permanent = True


def logout():
    session.clear()


def current_user():
    pid = session.get("pid")
    if not pid:
        return None
    row = db.query(
        """SELECT p.*, h.household_name
           FROM participants p
           LEFT JOIN households h ON h.id = p.household_id
           WHERE p.id = ? AND p.access_enabled = 1""",
        (pid,),
        one=True,
    )
    return row


def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not g.get("user"):
            return redirect(url_for("access.login"))
        return fn(*args, **kwargs)
    return wrapped


def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        user = g.get("user")
        if not user:
            return redirect(url_for("access.login"))
        if user["role"] != "admin":
            flash("That action is admin-only.", "error")
            abort(403)
        return fn(*args, **kwargs)
    return wrapped

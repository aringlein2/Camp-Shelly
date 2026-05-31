"""Camp Shelly Hub — Flask app factory."""
import os
import re
from flask import Flask, g, redirect, url_for, request, send_from_directory, abort

from . import db
from .auth import current_user
from .blueprints import (
    access,
    dashboard,
    announcements,
    posts,
    gear,
    meals,
    rides,
    activities,
    faq,
    packing,
    lost_found,
    search,
    admin,
)


def create_app():
    app = Flask(__name__, instance_relative_config=False)

    data_dir = os.environ.get(
        "DATABASE_PATH",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "camp_shelly.db"),
    )
    upload_dir = os.path.join(os.path.dirname(data_dir), "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
        DATABASE=data_dir,
        UPLOAD_DIR=upload_dir,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,  # 5 MB upload cap
        TRIP_INFO={
            "name": os.environ.get("CAMP_NAME", "Camp Shelly"),
            "dates": os.environ.get("CAMP_DATES", "Trip dates TBD"),
            "location": os.environ.get("CAMP_LOCATION", "Location TBD"),
            "welcome": os.environ.get("CAMP_WELCOME", "Welcome to Camp Shelly Hub."),
            "weather_url": os.environ.get("WEATHER_URL", ""),
            "rules_url": os.environ.get("RULES_URL", ""),
            "printable_url": os.environ.get("PRINTABLE_URL", ""),
        },
        ADMIN_PHONE=os.environ.get("ADMIN_PHONE", ""),
        ADMIN_NAME=os.environ.get("ADMIN_NAME", "Admin"),
        ADMIN_HOUSEHOLD=os.environ.get("ADMIN_HOUSEHOLD", "Admin Household"),
    )

    db.init_app(app)

    app.register_blueprint(access.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(announcements.bp)
    app.register_blueprint(posts.bp)
    app.register_blueprint(gear.bp)
    app.register_blueprint(meals.bp)
    app.register_blueprint(rides.bp)
    app.register_blueprint(activities.bp)
    app.register_blueprint(faq.bp)
    app.register_blueprint(packing.bp)
    app.register_blueprint(lost_found.bp)
    app.register_blueprint(search.bp)
    app.register_blueprint(admin.bp)

    @app.before_request
    def load_user():
        g.user = current_user()
        if not g.user:
            if request.endpoint and (
                request.endpoint.startswith("access.")
                or request.endpoint == "static"
                or request.endpoint == "robots"
            ):
                return None
            return redirect(url_for("access.login"))

    @app.context_processor
    def inject_globals():
        return {
            "current_user": g.get("user"),
            "trip": app.config["TRIP_INFO"],
        }

    @app.route("/robots.txt")
    def robots():
        return ("User-agent: *\nDisallow: /\n", 200, {"Content-Type": "text/plain"})

    # Serve uploaded images (login-gated by the global before_request hook above)
    @app.route("/uploads/<path:filename>")
    def uploads(filename):
        # only allow safe filenames (no slashes, dots-dot)
        if not re.fullmatch(r"[A-Za-z0-9_\-]+\.(jpg|jpeg|png|webp)", filename):
            abort(404)
        return send_from_directory(app.config["UPLOAD_DIR"], filename)

    with app.app_context():
        db.init_db()
        from .seed import seed_initial_data
        seed_initial_data(app)

    return app

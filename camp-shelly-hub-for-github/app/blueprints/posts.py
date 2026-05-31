from flask import Blueprint, render_template, request, redirect, url_for, g, flash, abort, current_app
from .. import db
from ..utils import POST_CATEGORIES, POST_TAGS
from ..views_tracker import mark_viewed
from ..images import save_resized, delete_image

bp = Blueprint("posts", __name__, url_prefix="/posts")


def _can_edit_post(post, user):
    return user["role"] == "admin" or post["author_id"] == user["id"]


@bp.route("/")
def index():
    category = request.args.get("category", "")
    sort = request.args.get("sort", "new")
    sql = """SELECT p.*, pa.display_name AS author_name,
                    (SELECT COUNT(*) FROM replies r WHERE r.post_id = p.id) AS reply_count
             FROM posts p LEFT JOIN participants pa ON pa.id = p.author_id"""
    args = []
    if category:
        sql += " WHERE p.category = ?"
        args.append(category)
    if sort == "replies":
        sql += " ORDER BY p.pinned DESC, reply_count DESC, p.created_at DESC"
    elif sort == "unresolved":
        sql += (" AND" if category else " WHERE") + " p.status = 'open'"
        sql += " ORDER BY p.pinned DESC, p.created_at DESC"
    else:
        sql += " ORDER BY p.pinned DESC, p.created_at DESC"
    items = db.query(sql, tuple(args))
    if g.get("user"):
        mark_viewed(g.user["id"], "posts")
    return render_template(
        "posts/index.html",
        items=items,
        categories=POST_CATEGORIES,
        category=category,
        sort=sort,
    )


@bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        category = request.form.get("category", "").strip()
        tags = ",".join(request.form.getlist("tags"))
        if not title or not body or category not in POST_CATEGORIES:
            flash("Title, body, and category are required.", "error")
            return render_template(
                "posts/edit.html", post=None,
                categories=POST_CATEGORIES, tags_options=POST_TAGS,
                selected_tags=request.form.getlist("tags"),
            )
        # Handle photo upload
        image_path = None
        photo = request.files.get("photo")
        try:
            image_path = save_resized(photo, current_app.config["UPLOAD_DIR"])
        except ValueError as e:
            flash(str(e), "error")
            return render_template(
                "posts/edit.html", post=None,
                categories=POST_CATEGORIES, tags_options=POST_TAGS,
                selected_tags=request.form.getlist("tags"),
            )
        new_id = db.execute(
            """INSERT INTO posts (title, body, category, tags, author_id, image_path)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, body, category, tags, g.user["id"], image_path),
        )
        return redirect(url_for("posts.detail", post_id=new_id))
    return render_template(
        "posts/edit.html", post=None,
        categories=POST_CATEGORIES, tags_options=POST_TAGS, selected_tags=[],
    )


@bp.route("/<int:post_id>")
def detail(post_id):
    post = db.query(
        """SELECT p.*, pa.display_name AS author_name
           FROM posts p LEFT JOIN participants pa ON pa.id = p.author_id
           WHERE p.id = ?""",
        (post_id,), one=True,
    )
    if not post:
        abort(404)
    replies = db.query(
        """SELECT r.*, pa.display_name AS author_name
           FROM replies r LEFT JOIN participants pa ON pa.id = r.author_id
           WHERE r.post_id = ? ORDER BY r.created_at ASC""",
        (post_id,),
    )
    return render_template("posts/detail.html", post=post, replies=replies)


@bp.route("/<int:post_id>/edit", methods=["GET", "POST"])
def edit(post_id):
    post = db.query("SELECT * FROM posts WHERE id = ?", (post_id,), one=True)
    if not post:
        abort(404)
    if not _can_edit_post(post, g.user):
        abort(403)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        category = request.form.get("category", "").strip()
        tags = ",".join(request.form.getlist("tags"))

        # Photo upload (replaces any existing)
        image_path = post["image_path"]
        photo = request.files.get("photo")
        try:
            new_img = save_resized(photo, current_app.config["UPLOAD_DIR"])
            if new_img:
                if image_path:
                    delete_image(image_path, current_app.config["UPLOAD_DIR"])
                image_path = new_img
        except ValueError as e:
            flash(str(e), "error")
            selected_tags = post["tags"].split(",") if post["tags"] else []
            return render_template(
                "posts/edit.html", post=post,
                categories=POST_CATEGORIES, tags_options=POST_TAGS,
                selected_tags=selected_tags,
            )

        # Optional remove-existing
        if request.form.get("remove_photo") and image_path:
            delete_image(image_path, current_app.config["UPLOAD_DIR"])
            image_path = None

        db.execute(
            """UPDATE posts SET title=?, body=?, category=?, tags=?, image_path=?,
               updated_at=CURRENT_TIMESTAMP WHERE id=?""",
            (title, body, category, tags, image_path, post_id),
        )
        return redirect(url_for("posts.detail", post_id=post_id))
    selected_tags = post["tags"].split(",") if post["tags"] else []
    return render_template(
        "posts/edit.html", post=post,
        categories=POST_CATEGORIES, tags_options=POST_TAGS, selected_tags=selected_tags,
    )


@bp.route("/<int:post_id>/delete", methods=["POST"])
def delete(post_id):
    post = db.query("SELECT * FROM posts WHERE id = ?", (post_id,), one=True)
    if not post:
        abort(404)
    if not _can_edit_post(post, g.user):
        abort(403)
    if post["image_path"]:
        delete_image(post["image_path"], current_app.config["UPLOAD_DIR"])
    db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    flash("Post deleted.", "success")
    return redirect(url_for("posts.index"))


@bp.route("/<int:post_id>/reply", methods=["POST"])
def reply(post_id):
    post = db.query("SELECT id FROM posts WHERE id = ?", (post_id,), one=True)
    if not post:
        abort(404)
    body = request.form.get("body", "").strip()
    if not body:
        flash("Reply can't be empty.", "error")
        return redirect(url_for("posts.detail", post_id=post_id))
    db.execute(
        "INSERT INTO replies (post_id, body, author_id) VALUES (?, ?, ?)",
        (post_id, body, g.user["id"]),
    )
    return redirect(url_for("posts.detail", post_id=post_id) + "#r-bottom")


@bp.route("/replies/<int:reply_id>/delete", methods=["POST"])
def delete_reply(reply_id):
    r = db.query("SELECT * FROM replies WHERE id = ?", (reply_id,), one=True)
    if not r:
        abort(404)
    if g.user["role"] != "admin" and r["author_id"] != g.user["id"]:
        abort(403)
    db.execute("DELETE FROM replies WHERE id = ?", (reply_id,))
    return redirect(url_for("posts.detail", post_id=r["post_id"]))


@bp.route("/<int:post_id>/status", methods=["POST"])
def set_status(post_id):
    post = db.query("SELECT * FROM posts WHERE id = ?", (post_id,), one=True)
    if not post:
        abort(404)
    if g.user["role"] != "admin" and post["author_id"] != g.user["id"]:
        abort(403)
    new_status = request.form.get("status", "open")
    if new_status not in ("open", "answered", "resolved"):
        abort(400)
    db.execute(
        "UPDATE posts SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (new_status, post_id),
    )
    return redirect(url_for("posts.detail", post_id=post_id))


@bp.route("/<int:post_id>/pin", methods=["POST"])
def pin(post_id):
    if g.user["role"] != "admin":
        abort(403)
    post = db.query("SELECT pinned FROM posts WHERE id = ?", (post_id,), one=True)
    if not post:
        abort(404)
    new_val = 0 if post["pinned"] else 1
    db.execute("UPDATE posts SET pinned=? WHERE id=?", (new_val, post_id))
    return redirect(url_for("posts.detail", post_id=post_id))

"""Photo upload handling: validate, resize, save, delete."""
import io
import os
import secrets
from PIL import Image, ImageOps

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
MAX_WIDTH = 1200


def is_allowed(filename):
    if not filename:
        return False
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXT


def save_resized(file_storage, upload_dir):
    """Read an uploaded image, downscale to MAX_WIDTH, save as JPEG.

    Returns the saved filename (no path), or None if input was empty/invalid.
    """
    if not file_storage or not file_storage.filename:
        return None
    if not is_allowed(file_storage.filename):
        raise ValueError("Only JPG, PNG, or WebP images are supported.")

    data = file_storage.read()
    if not data:
        return None
    try:
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img)  # honor rotation metadata
    except Exception:
        raise ValueError("That file doesn't look like a valid image.")

    if img.width > MAX_WIDTH:
        ratio = MAX_WIDTH / img.width
        new_size = (MAX_WIDTH, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    # Always save as JPEG for size; convert if needed
    if img.mode in ("RGBA", "P"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")

    filename = secrets.token_urlsafe(12).replace("-", "_") + ".jpg"
    out_path = os.path.join(upload_dir, filename)
    img.save(out_path, format="JPEG", quality=85, optimize=True)
    return filename


def delete_image(filename, upload_dir):
    if not filename:
        return
    path = os.path.join(upload_dir, filename)
    try:
        os.remove(path)
    except FileNotFoundError:
        pass

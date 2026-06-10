"""
image_handler.py
----------------
Handles all image concerns for Flourisha:
  • Validating uploaded files
  • Saving to disk under a per-user directory
  • Generating thumbnail versions
  • Linking saved images back to a Plant record
  • Preparing the image for PlantNet (bytes / base64)

Dependencies:
    pip install Pillow
"""

import os
import uuid
import logging
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration defaults (override via Flask app.config)
# ---------------------------------------------------------------------------

UPLOAD_FOLDER      = os.getenv("UPLOAD_FOLDER", "uploads")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_DIMENSION      = 1600      # pixels — images are down-scaled if larger
THUMBNAIL_SIZE     = (400, 400)
JPEG_QUALITY       = 85


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _make_dirs(*parts: str) -> Path:
    path = Path(*parts)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _unique_stem() -> str:
    return uuid.uuid4().hex


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def validate_upload(file: FileStorage) -> Tuple[bool, str]:
    """
    Check that the upload is a valid image file.

    Returns:
        (True, "")          on success
        (False, "reason")   on failure
    """
    if not file or not file.filename:
        return False, "No file received."

    if not _allowed(file.filename):
        return False, (
            f"Unsupported file type. Please upload one of: "
            f"{', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )

    # Quick magic-bytes check — reads just the first 12 bytes
    header = file.stream.read(12)
    file.stream.seek(0)

    MAGIC = {
        b"\xff\xd8\xff"          : "jpeg",
        b"\x89PNG\r\n\x1a\n"    : "png",
        b"RIFF"                  : "webp",  # RIFF....WEBP
    }
    recognised = any(header.startswith(sig) for sig in MAGIC)
    if not recognised:
        return False, "File does not appear to be a valid image."

    return True, ""


def save_upload(
    file: FileStorage,
    user_id: Optional[int] = None,
    base_folder: str = UPLOAD_FOLDER,
) -> dict:
    """
    Save a validated FileStorage object to disk.

    Directory layout:
        uploads/
          user_<user_id>/   ← registered users
          guest/            ← anonymous uploads

    Returns a dict:
        {
          "relative_path": "user_42/abc123.jpg",   # stored in Plant.image_url
          "absolute_path": "/abs/path/to/file.jpg",
          "thumbnail_path": "user_42/abc123_thumb.jpg",
          "filename": "abc123.jpg",
        }
    """
    sub = f"user_{user_id}" if user_id else "guest"
    folder = _make_dirs(base_folder, sub)

    stem      = _unique_stem()
    ext       = file.filename.rsplit(".", 1)[1].lower()
    ext       = "jpg" if ext == "jpeg" else ext   # normalise
    filename  = f"{stem}.{ext}"
    abs_path  = folder / filename

    # ── Open with Pillow, resize if needed, save ───────────────────────────
    try:
        img = Image.open(file.stream)
        img = img.convert("RGB")   # strip alpha / CMYK, ensures JPEG compat

        # Downscale large images to save space and speed up PlantNet
        if max(img.size) > MAX_DIMENSION:
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

        save_kwargs = {"quality": JPEG_QUALITY, "optimize": True} if ext == "jpg" else {}
        img.save(str(abs_path), **save_kwargs)

        # ── Thumbnail ──────────────────────────────────────────────────────
        thumb_filename = f"{stem}_thumb.{ext}"
        thumb_path     = folder / thumb_filename
        thumb          = img.copy()
        thumb.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)
        thumb.save(str(thumb_path), **save_kwargs)

    except Exception as exc:
        logger.error("Image save failed: %s", exc)
        raise RuntimeError(f"Could not process image: {exc}") from exc

    rel       = f"{sub}/{filename}"
    thumb_rel = f"{sub}/{thumb_filename}"

    logger.info("Image saved → %s", rel)

    return {
        "relative_path" : rel,
        "absolute_path" : str(abs_path),
        "thumbnail_path": thumb_rel,
        "filename"      : filename,
    }


def read_image_bytes(absolute_path: str) -> bytes:
    """
    Read an image from disk and return raw bytes.
    Used when sending the image to PlantNet via multipart upload.
    """
    with open(absolute_path, "rb") as fh:
        return fh.read()


def link_image_to_plant(plant, image_info: dict):
    """
    Convenience helper — sets Plant.image_url from a save_upload() result dict
    and commits.  Import db here to avoid circular imports.
    """
    from extensions import db   # local import to avoid circulars

    plant.image_url = image_info["relative_path"]
    db.session.commit()
    logger.info("Plant id=%s linked to image '%s'.", plant.id, plant.image_url)


def delete_image(relative_path: str, base_folder: str = UPLOAD_FOLDER):
    """
    Delete an image (and its thumbnail if it exists) from disk.
    Safe to call even if the file is already missing.
    """
    for path in [
        Path(base_folder) / relative_path,
        Path(base_folder) / relative_path.replace(".", "_thumb."),
    ]:
        try:
            path.unlink(missing_ok=True)
        except Exception as exc:
            logger.warning("Could not delete '%s': %s", path, exc)
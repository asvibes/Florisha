"""
utils/cloudinary_helper.py
--------------------------
Handles all Cloudinary image operations for Flourisha.
"""

import os
import cloudinary
import cloudinary.uploader

# Configure Cloudinary from environment variables
cloudinary.config(
    cloud_name  = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key     = os.getenv("CLOUDINARY_API_KEY"),
    api_secret  = os.getenv("CLOUDINARY_API_SECRET"),
    secure      = True,
)


def upload_image(file_stream, public_id=None):
    """
    Upload an image file stream to Cloudinary.

    Returns:
        str — the secure URL of the uploaded image
    Raises:
        RuntimeError if upload fails
    """
    try:
        result = cloudinary.uploader.upload(
            file_stream,
            folder      = "flourisha",
            public_id   = public_id,
            overwrite   = True,
            resource_type = "image",
        )
        return result["secure_url"]
    except Exception as e:
        raise RuntimeError(f"Cloudinary upload failed: {e}") from e


def delete_image(image_url):
    """
    Delete an image from Cloudinary using its URL.
    Safe to call even if the image doesn't exist.
    """
    if not image_url or not image_url.startswith("http"):
        return  # skip local paths or empty values

    try:
        # Extract public_id from URL
        # URL format: https://res.cloudinary.com/<cloud>/image/upload/v123/flourisha/<id>.jpg
        parts    = image_url.split("/")
        filename = parts[-1]                        # e.g. "abc123.jpg"
        stem     = filename.rsplit(".", 1)[0]       # e.g. "abc123"
        folder   = parts[-2]                        # e.g. "flourisha"
        public_id = f"{folder}/{stem}"

        cloudinary.uploader.destroy(public_id)
    except Exception:
        pass  # never crash over a failed delete
import os
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile


def optimize_image_field(image_field, max_width=1800, quality=84):
    if not image_field:
        return

    try:
        from PIL import Image, ImageOps
    except ImportError:
        return

    try:
        image_field.open("rb")
        with Image.open(image_field) as image:
            image = ImageOps.exif_transpose(image)
            original_format = image.format or "JPEG"

            if image.width > max_width:
                ratio = max_width / float(image.width)
                new_size = (max_width, int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            output = BytesIO()
            filename = Path(image_field.name).name
            extension = Path(filename).suffix.lower()

            if extension in {".jpg", ".jpeg"}:
                if image.mode not in {"RGB", "L"}:
                    image = image.convert("RGB")
                image.save(output, format="JPEG", quality=quality, optimize=True)
            elif extension == ".png":
                image.save(output, format="PNG", optimize=True)
            elif extension == ".webp":
                image.save(output, format="WEBP", quality=quality, optimize=True)
            else:
                if image.mode not in {"RGB", "L"}:
                    image = image.convert("RGB")
                image.save(output, format=original_format, quality=quality, optimize=True)

            image_field.save(filename, ContentFile(output.getvalue()), save=False)
    except (OSError, ValueError):
        return
    finally:
        try:
            image_field.close()
        except Exception:
            pass


def remove_old_file(path):
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass

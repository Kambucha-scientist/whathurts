import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}


def _upload_dir() -> str:
    path = os.path.join(current_app.static_folder, "uploads", "medicines")
    os.makedirs(path, exist_ok=True)
    return path


def save_medicine_image(file_storage) -> str | None:
    """Сохраняет файл и возвращает его имя (без пути). None — если файл не передан."""
    if not file_storage or not getattr(file_storage, "filename", ""):
        return None
    original = secure_filename(file_storage.filename)
    if "." not in original:
        raise ValueError("Файл без расширения")
    ext = original.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Недопустимый формат изображения")
    unique = f"{uuid.uuid4().hex}.{ext}"
    file_storage.save(os.path.join(_upload_dir(), unique))
    return unique


def delete_medicine_image(filename: str | None) -> None:
    if not filename:
        return
    path = os.path.join(_upload_dir(), filename)
    if os.path.isfile(path):
        try:
            os.remove(path)
        except OSError:
            current_app.logger.warning("Не удалось удалить файл %s", path)
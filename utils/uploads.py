import os
import uuid

from flask import current_app


def allowed_nid_file(filename):
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_NID_EXTENSIONS"]


def save_nid_file(file, side):
    if file is None or file.filename == "":
        return None

    if not allowed_nid_file(file.filename):
        return None

    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}_{side}.{ext}"

    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)

    file.save(os.path.join(folder, filename))
    return filename
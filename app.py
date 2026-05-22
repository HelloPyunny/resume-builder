from io import BytesIO
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

from builder import (
    BASE_DIR,
    UPLOAD_DIR,
    default_data,
    generate_pdf_bytes,
    load_data,
    next_output_path,
    save_data,
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("editor.html")


@app.route("/api/data", methods=["GET"])
def get_data():
    return jsonify(load_data())


@app.route("/api/data", methods=["POST"])
def post_data():
    data = request.get_json(force=True)
    save_data(data)
    return jsonify({"ok": True})


@app.route("/api/photo", methods=["POST"])
def upload_photo():
    if "photo" not in request.files:
        return jsonify({"error": "No photo file."}), 400

    file = request.files["photo"]
    if not file.filename:
        return jsonify({"error": "Empty filename."}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Only jpg, png, webp allowed."}), 400

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename).suffix.lower()
    filename = secure_filename(f"profile{ext}")
    save_path = UPLOAD_DIR / filename
    file.save(save_path)

    data = load_data()
    data["photo"] = f"uploads/{filename}"
    save_data(data)

    return jsonify({"ok": True, "photo": data["photo"]})


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_file(UPLOAD_DIR / filename)


def _pdf_from_data(data: dict, *, attachment: bool, download_name: str):
    pdf_bytes = generate_pdf_bytes(data)
    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=attachment,
        download_name=download_name if attachment else None,
    )


@app.route("/api/preview", methods=["POST"])
def api_preview():
    data = request.get_json(force=True)
    return _pdf_from_data(data, attachment=False, download_name="preview.pdf")


@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.get_json(force=True) if request.is_json else load_data()
    save_data(data)
    path = next_output_path(BASE_DIR)
    path.write_bytes(generate_pdf_bytes(data))
    return _pdf_from_data(data, attachment=True, download_name=path.name)


if __name__ == "__main__":
    if not (BASE_DIR / "resume_data.json").exists():
        save_data(default_data())
    UPLOAD_DIR.mkdir(exist_ok=True)
    print("Open http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)

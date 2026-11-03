import os
import uuid
from io import BytesIO
from urllib.parse import urlsplit, unquote

import cloudinary
import cloudinary.api
import cloudinary.uploader
from flask import Flask, flash, redirect, render_template, request, url_for
from PIL import Image, ImageOps, UnidentifiedImageError

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cambiar-en-render-antes-del-evento")
app.config["MAX_CONTENT_LENGTH"] = 80 * 1024 * 1024

EVENT_NAME = os.environ.get("EVENT_NAME", 'Velada "Una Generación que Responden"')
EVENT_MOTTO = "Jóvenes que inspiran, sirven y transforman"
EVENT_VERSE = "1 Timoteo 4:12"
FOLDER = os.environ.get("CLOUDINARY_FOLDER", "fotoevento").strip().strip("/")
MAX_FILES = 15

# Admite CLOUDINARY_URL o las tres variables separadas en Render.
url = os.environ.get("CLOUDINARY_URL", "").strip()
if url:
    parts = urlsplit(url)
    if parts.scheme != "cloudinary" or not all([parts.hostname, parts.username, parts.password]):
        raise RuntimeError("CLOUDINARY_URL no tiene el formato cloudinary://API_KEY:API_SECRET@CLOUD_NAME")
    cloudinary.config(
        cloud_name=parts.hostname,
        api_key=unquote(parts.username),
        api_secret=unquote(parts.password),
        secure=True,
    )
else:
    cloudinary.config(
        cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME", "").strip(),
        api_key=os.environ.get("CLOUDINARY_API_KEY", "").strip(),
        api_secret=os.environ.get("CLOUDINARY_API_SECRET", "").strip(),
        secure=True,
    )

def cloudinary_ready():
    cfg = cloudinary.config()
    return bool(cfg.cloud_name and cfg.api_key and cfg.api_secret)

@app.get("/")
def index():
    photos = []
    error = None
    if not cloudinary_ready():
        error = "Falta configurar Cloudinary en Render."
    else:
        try:
            result = cloudinary.api.resources(
                type="upload", resource_type="image",
                prefix=FOLDER + "/", max_results=100, direction="desc",
            )
            photos = [r["secure_url"] for r in result.get("resources", []) if r.get("secure_url")]
        except Exception:
            app.logger.exception("No se pudo consultar Cloudinary")
            error = "No se pudo cargar la galería. Revisa los Logs de Render."
    return render_template(
        "index.html", photos=photos, error=error,
        event_name=EVENT_NAME, event_motto=EVENT_MOTTO, event_verse=EVENT_VERSE,
    )

@app.post("/subir")
def upload():
    if not cloudinary_ready():
        flash("Cloudinary no está configurado.", "error")
        return redirect(url_for("index"))
    files = [f for f in request.files.getlist("fotos") if f.filename]
    if not files or len(files) > MAX_FILES:
        flash("Selecciona entre 1 y 15 fotografías.", "error")
        return redirect(url_for("index"))
    count = 0
    for file in files:
        try:
            image = Image.open(file.stream)
            image.verify()
            file.stream.seek(0)
            image = Image.open(file.stream)
            image.load()
            if image.width * image.height > 50_000_000:
                continue
            image = ImageOps.exif_transpose(image).convert("RGB")
            image.thumbnail((2400, 2400))
            output = BytesIO()
            image.save(output, format="JPEG", quality=85, optimize=True)
            output.seek(0)
            cloudinary.uploader.upload(
                output, folder=FOLDER, public_id=uuid.uuid4().hex,
                resource_type="image", format="jpg", overwrite=False,
            )
            count += 1
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
            app.logger.warning("Archivo de imagen inválido omitido")
        except Exception:
            app.logger.exception("Error al subir fotografía")
    flash(f"Se compartieron {count} foto(s)." if count else
          "No se pudieron subir las fotografías. Revisa los Logs de Render.",
          "success" if count else "error")
    return redirect(url_for("index"))

@app.errorhandler(413)
def too_large(error):
    flash("El envío supera 80 MB. Selecciona menos fotografías.", "error")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=False, port=int(os.environ.get("PORT", "5000")))

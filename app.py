import os
import uuid
from io import BytesIO

import cloudinary
import cloudinary.api
import cloudinary.uploader
from flask import Flask, flash, redirect, render_template, request, url_for
from PIL import Image, ImageOps, UnidentifiedImageError

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'solo-desarrollo-cambiar')
app.config['MAX_CONTENT_LENGTH'] = 80 * 1024 * 1024
app.config['EVENT_NAME'] = os.environ.get('EVENT_NAME', 'Nuestro evento')

cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET'),
    secure=True,
)
FOLDER = os.environ.get('CLOUDINARY_FOLDER', 'fotoevento')
MAX_FILES = 15

@app.get('/')
def index():
    photos = []
    error = None
    try:
        # Lista las 100 imágenes más recientes. No requiere base de datos local.
        result = cloudinary.api.resources(type='upload', resource_type='image',
                                          prefix=FOLDER + '/', max_results=100,
                                          direction='desc')
        photos = [r['secure_url'] for r in result.get('resources', [])]
    except Exception:
        app.logger.exception('No se pudo consultar Cloudinary')
        error = 'No se pudo cargar la galería. Revisa la configuración de Cloudinary.'
    return render_template('index.html', photos=photos,
                           event_name=app.config['EVENT_NAME'], error=error)

@app.post('/subir')
def upload():
    files = [f for f in request.files.getlist('fotos') if f.filename]
    if not files or len(files) > MAX_FILES:
        flash('Selecciona entre 1 y 15 fotografías.')
        return redirect(url_for('index'))
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
            image = ImageOps.exif_transpose(image).convert('RGB')
            image.thumbnail((2400, 2400))
            output = BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            cloudinary.uploader.upload(
                output, folder=FOLDER, public_id=uuid.uuid4().hex,
                resource_type='image', format='jpg', overwrite=False,
            )
            count += 1
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
            continue
        except Exception:
            app.logger.exception('Error al subir fotografía')
    flash(f'Se compartieron {count} foto(s).' if count else 'No se pudieron subir las fotografías.')
    return redirect(url_for('index'))

@app.errorhandler(413)
def too_large(error):
    flash('El envío supera 80 MB. Selecciona menos fotografías.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=False, port=int(os.environ.get('PORT', '5000')))

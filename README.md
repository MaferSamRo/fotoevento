# FotoEvento para internet (Render + Cloudinary)

## 1. Cloudinary
1. Registra una cuenta en https://cloudinary.com/
2. En la consola localiza **Cloud name**, **API key** y **API secret**. Mantén el secret privado.

## 2. GitHub
Crea un repositorio privado y sube `app.py`, `requirements.txt`, `templates/index.html` y `.gitignore` (no subas `.env` ni credenciales).

## 3. Render
1. Ve a https://dashboard.render.com/ > New > Web Service y conecta el repositorio.
2. Runtime/Language: Python. Build command: `pip install -r requirements.txt`.
3. Start command: `gunicorn app:app`.
4. En Environment agrega:
   - `CLOUDINARY_CLOUD_NAME`: tu cloud name
   - `CLOUDINARY_API_KEY`: tu API key
   - `CLOUDINARY_API_SECRET`: tu API secret
   - `SECRET_KEY`: una cadena aleatoria larga
   - `EVENT_NAME`: nombre de tu evento
   - `CLOUDINARY_FOLDER`: fotoevento (opcional)
5. Haz Deploy. Render generará una URL HTTPS pública.

## 4. Probar
Abre la URL desde dos celulares, uno con Wi-Fi y otro con datos móviles. Sube una imagen y comprueba que aparece en ambos después de actualizar (o esperar 15 segundos). Reinicia el servicio y comprueba que permanece.

## Limitaciones y seguridad
- La galería muestra las **100 imágenes más recientes**. Para eventos más grandes hay que añadir paginación o base de datos.
- La galería es pública para quien tenga la URL; no hay cuentas ni moderación.
- La subida es pública: antes de distribuir el QR, añadir rate limiting, CAPTCHA, moderación y un control de administrador para retirar contenido.
- El servidor usa la API de administración de Cloudinary para listar las fotos: vigila los límites de tu plan.
- Las fotos se convierten a JPEG y se reducen a 2400 píxeles como máximo por lado; no se admiten vídeos.
- Los planes y límites de Render y Cloudinary pueden cambiar; revísalos antes de elegir.

from io import BytesIO
from os.path import splitext
from uuid import uuid4

from flask_uploads import IMAGES, UploadNotAllowed, UploadSet, configure_uploads
from PIL import Image, UnidentifiedImageError
from werkzeug.datastructures import FileStorage

uploaded_logos = UploadSet('logos', IMAGES)

common_extensions = {
    'JPEG': '.jpg',
    'JPEG2000': '.jp2',
    'GIF': '.gif',
    'PNG': '.png',
    'WEBP': '.webp',
}


def configure(app):
    configure_uploads(app, uploaded_logos)


def image_extension(img_format):
    if img_format in common_extensions:
        return common_extensions[img_format]
    for extension, ext_format in Image.EXTENSION.items():
        if img_format == ext_format:
            return extension
    return '.unknown'


def process_image(requestfile, maxsize=(170, 130)):
    fileext = splitext(requestfile.filename)[1].lower()
    if fileext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        raise UploadNotAllowed("Unsupported file format")
    try:
        img = Image.open(requestfile)
    except UnidentifiedImageError:
        raise UploadNotAllowed("Unsupported file format")
    except Image.DecompressionBombError:
        raise UploadNotAllowed("This image is too large to process")
    img.load()
    if img.size[0] > maxsize[0] or img.size[1] > maxsize[1]:
        img.thumbnail(maxsize, Image.ANTIALIAS)
    boximg = Image.new(img.mode, maxsize, '#fff0')
    boximg.paste(
        img, ((boximg.size[0] - img.size[0]) // 2, (boximg.size[1] - img.size[1]) // 2)
    )
    savefile = BytesIO()
    savefile.name = uuid4().hex + image_extension(img.format)
    boximg.save(savefile, img.format)
    savefile.seek(0)
    return FileStorage(
        savefile, filename=savefile.name, content_type=Image.MIME[img.format]
    )

# -*- coding: utf-8 -*-

from PIL import Image
from io import StringIO
from os.path import splitext
from werkzeug.datastructures import FileStorage

from flask_uploads import UploadSet, configure_uploads, IMAGES, UploadNotAllowed

from hasjob import app

uploaded_logos = UploadSet('logos', IMAGES)


def configure():
    configure_uploads(app, uploaded_logos)


def process_image(requestfile, maxsize=(170, 130)):
    fileext = splitext(requestfile.filename)[1].lower()
    if fileext not in ['.jpg', '.jpeg', '.png', '.gif']:
        raise UploadNotAllowed("Unsupported file format")
    img = Image.open(requestfile)
    img.load()
    if img.size[0] > maxsize[0] or img.size[1] > maxsize[1]:
        img.thumbnail(maxsize, Image.ANTIALIAS)
    boximg = Image.new('RGBA', maxsize, (255, 255, 255, 0))
    boximg.paste(img, ((boximg.size[0] - img.size[0]) // 2, (boximg.size[1] - img.size[1]) // 2))
    savefile = StringIO()
    savefile.name = requestfile.filename
    boximg.save(savefile)
    savefile.seek(0)
    return FileStorage(savefile,
        filename=requestfile.filename,
        content_type=requestfile.content_type)

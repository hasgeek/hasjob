import Image
from StringIO import StringIO
from os.path import splitext
from werkzeug import FileStorage

from flask import request
from flaskext.uploads import UploadSet, configure_uploads, IMAGES, UploadNotAllowed
from app import app

uploaded_logos = UploadSet('logos', IMAGES)

def configure():
    configure_uploads(app, uploaded_logos)

def process_image(requestfile, maxsize=170):
    img = Image.open(requestfile)
    img.load()
    if img.size[0] > maxsize or img.size[1] > maxsize:
        img.thumbnail((maxsize, maxsize), Image.ANTIALIAS)
    boximg = Image.new('RGBA', (maxsize, maxsize), (255, 255, 255, 0))
    boximg.paste(img, ((boximg.size[0]-img.size[0])/2, (boximg.size[1]-img.size[1])/2))
    savefile = StringIO()
    savefile.name = requestfile.filename
    boximg.save(savefile)
    savefile.seek(0)
    return FileStorage(savefile,
        filename=requestfile.filename,
        content_type=requestfile.content_type)

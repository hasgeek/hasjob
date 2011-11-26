from StringIO import StringIO
from werkzeug import FileStorage
from flaskext.uploads import UploadSet, configure_uploads, \
                                IMAGES
from application import app

import Image


uploaded_logos = UploadSet('logos', IMAGES)


def configure():
    configure_uploads(app, uploaded_logos)


def process_image(requestfile, maxsize=(170, 130)):
    img = Image.open(requestfile)
    img.load()
    if img.size[0] > maxsize[0] or img.size[1] > maxsize[1]:
        img.thumbnail(maxsize, Image.ANTIALIAS)
    boximg = Image.new('RGBA', maxsize, (255, 255, 255, 0))
    boximg.paste(img, ((boximg.size[0] - img.size[0]) / 2,
                    (boximg.size[1] - img.size[1]) / 2))
    savefile = StringIO()
    savefile.name = requestfile.filename
    boximg.save(savefile)
    savefile.seek(0)
    return FileStorage(savefile,
        filename=requestfile.filename,
        content_type=requestfile.content_type)

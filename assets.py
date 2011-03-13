from flaskext.assets import Environment, Bundle
from app import app

assets = Environment(app)

js = Bundle('js/libs/jquery-1.5.1.min.js',
            'js/libs/jquery.textarea-expander.js',
            'js/scripts.js',
            filters='jsmin', output='js/packed.js')

assets.register('js_all', js)

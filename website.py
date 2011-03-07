#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app import app
import models, forms, views

app.config.from_object(__name__)
try:
    app.config.from_object('settings')
except ImportError:
    import sys
    print >> sys.stderr, "Please create a settings.py with the necessary settings. See settings-sample.py."
    print >> sys.stderr, "You may use the site without these settings, but some features may not work."


if __name__ == '__main__':
    app.run(debug=True)

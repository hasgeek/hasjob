# -*- coding: utf-8 -*-

"""
Natural language processing helpers.
"""

import langid
import bleach

def identify_language(post):
    return langid.classify(u'\n'.join([post.headline, bleach.clean(post.description, tags=[], strip=True)]))[0]

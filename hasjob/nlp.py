# -*- coding: utf-8 -*-

"""
Natural language processing helpers.
"""

import bleach
import langid


def identify_language(post):
    return langid.classify(
        '\n'.join([post.headline, bleach.clean(post.description, tags=[], strip=True)])
    )

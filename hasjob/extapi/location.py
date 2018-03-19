# -*- coding: utf-8 -*-

from urlparse import urljoin
import requests
from baseframe import cache
from .. import app


@cache.memoize(timeout=86400)
def location_geodata(location):
    if 'HASCORE_SERVER' in app.config and location:
        if isinstance(location, (list, tuple)):
            url = urljoin(app.config['HASCORE_SERVER'], '/1/geo/get_by_names')
        else:
            url = urljoin(app.config['HASCORE_SERVER'], '/1/geo/get_by_name')
        response = requests.get(url, params={'name': location}).json()
        if response.get('status') == 'ok':
            result = response.get('result', {})
            if isinstance(result, (list, tuple)):
                result = {r['geonameid']: r for r in result}
            return result
    return {}

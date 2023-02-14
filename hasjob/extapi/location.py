from urllib.parse import urljoin

import requests

from baseframe import cache

from .. import app


@cache.memoize(timeout=86400)
def location_geodata(location):
    if location:
        if isinstance(location, (list, tuple)):
            url = urljoin(app.config['LASTUSER_SERVER'], '/api/1/geo/get_by_names')
        else:
            url = urljoin(app.config['LASTUSER_SERVER'], '/api/1/geo/get_by_name')
        try:
            response = requests.get(url, params={'name': location}).json()
        except requests.exceptions.JSONDecodeError:
            return {}
        if response.get('status') == 'ok':
            result = response.get('result', {})
            if isinstance(result, (list, tuple)):
                result = {r['geonameid']: r for r in result}
            return result
    return {}

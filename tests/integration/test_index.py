from flask import url_for


class TestIndexView:
    def test_index(self, test_client, test_db):
        with test_client as c:
            resp = c.get(url_for('index', subdomain=None))
            assert "Hasjob" in resp.data.decode('utf-8')

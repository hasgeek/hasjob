import unittest
import mechanize
from flask.ext.testing import TestCase, Twill
from hasjob import app, init_for
from hasjob.models import db


# Base setup to run tests
class TestBase(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        db.create_all()
        init_for('testing')
        self.br = mechanize.Browser()
        return app

    def tearDown(self):
        db.session.remove()
        db.drop_all()


class TestWorkflow(TestBase):
    def test_index(self):
        with Twill(self.app, port=5000) as t:
            t.browser.go(t.url('/'))

    def test_new_listing(self):
        with Twill(self.app, port=5000) as t:
            t.browser.go(t.url('/new'))

    def test_static(self):
        with Twill(self.app, port=5000) as t:
            t.browser.go(t.url('/toc'))

    def test_stats(self):
        with Twill(self.app, port=5000) as t:
            t.browser.go(t.url('/stats'))

    def test_404(self):
        with Twill(self.app, port=5000) as t:
            t.browser.go(t.url('/blah'))


if __name__ == '__main__':
    unittest.main()

import unittest
from flaskext.testing import TestCase, Twill
from website import app, db

# Base setup to run tests
class TestBase(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

class TestWorkflow(TestBase):
    def test_new_listing_with_twill(self):
        with Twill(self.app, port=5000) as t:
            t.browser.go(t.url('/'))

if __name__=='__main__':
    unittest.main()

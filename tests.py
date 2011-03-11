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

if __name__=='__main__':
    unittest.main()

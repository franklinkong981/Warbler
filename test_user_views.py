"""Unit/integration tests for routes/view functions that have to do with the User model, such as the User profile page, followers page, etc."""

# run these tests like:
#
#    FLASK_ENV=production python3 -m unittest test_user_views.py

import os
from unittest import TestCase
from app import create_app, CURR_USER_KEY

from models import db, connect_db, User, Message, Follows, Likes
from sqlalchemy.exc import IntegrityError

# Create another application instance that connects to the testing database (warbler_test) instead of the main database (warbler).
app = create_app("warbler_test", testing=True)
connect_db(app)
app.app_context().push()

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

class UserViewsTestCase(TestCase):
    """Test views that have to do with User model."""

    def setUp(self):
        """Before each test, delete any existing data in the tables, create test client, store sample user in users table."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()
    
    def tearDown(self):
        """After each test, revert each table back to original state."""
        db.session.rollback()
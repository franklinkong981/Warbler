"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from app import create_app

from models import db, connect_db, User, Message, Follows, Likes

# Create another application instance that connects to the testing database (warbler_test) instead fo the main database (warbler).
app = create_app("warbler_test", testing=True)
connect_db(app)
app.app_context().push()

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

class UserModelTestCase(TestCase):
    """Test views for user model."""

    def setUp(self):
        """Before each test, delete any existing data in the tables, create test client, store sample user in users table."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()

        user1 = User(
            email="user1@test.com",
            username="user1",
            password="HASHED_PASSWORD1"
        )

        user2 = User(
            email="user2@test.com",
            username="user2",
            password="HASHED_PASSWORD2"
        )

        user3 = User(
            email="user3@test.com",
            username="user3",
            password="HASHED_PASSWORD3"
        )

        db.session.add_all([user1, user2, user3])
        db.session.commit()

    
    def tearDown(self):
        """After each test, revert each table back to original state."""
        db.session.rollback()

    def test_basic(self):
        """Does basic user model work?"""

        # User should have no messages & no followers
        user1 = User.query.filter(User.username == 'user1').first()
        self.assertEqual(len(user1.messages), 0)
        self.assertEqual(len(user1.followers), 0)
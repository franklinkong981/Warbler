"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from app import create_app

from models import db, connect_db, User, Message, Follows, Likes

# Create another application instance that connects to the testing database (warbler_test) instead of the main database (warbler).
app = create_app("warbler_test", testing=True)
connect_db(app)
app.app_context().push()

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

class MessageModelTestCase(TestCase):
    """Test views for messages model."""

    def setUp(self):
        """Before each test, delete any existing data in the tables, create test client, store sample user in users table."""
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()

        user1 = User.signup(
            email="user1@test.com",
            username="user1",
            password="HASHED_PASSWORD1",
            image_url="www.testurl1.com"
        )

        db.session.commit()

    def tearDown(self):
        """After each test, revert each table back to original state."""
        db.session.rollback()

    def test_message_model(self):
        """Does basic Message model work?"""

        user1 = User.query.filter(User.username == 'user1').first()
        message = Message(
            text="a warble",
            user_id=user1.id
        )

        db.session.add(message)
        db.session.commit()

        # User should have 1 message
        self.assertEqual(len(user1.messages), 1)
        self.assertEqual(user1.messages[0].user_id, user1.id)
        self.assertEqual(user1.messages[0].text, "a warble")

    def test_message_likes(self):
        """When a user likes another user's message/warble, does the message become part of the user's likes?"""
        user1 = User.query.filter(User.username == 'user1').first()
        message1 = Message(
            text="a warble",
            user_id=user1.id
        )

        message2 = Message(
            text="a very interesting warble",
            user_id=user1.id
        )

        user2 = User.signup("yetanothertest", "t@email.com", "password", None)
        db.session.add_all([message1, message2, user2])
        db.session.commit()

        user2.likes.append(message1)

        db.session.commit()

        # User 2 should have message 1 in their likes, NOT message 2.
        user2_likes = Likes.query.filter(Likes.user_id == user2.id).all()
        self.assertEqual(len(user2_likes), 1)
        user2_liked_message_ids = [message.id for message in user2_likes]
        self.assertIn(message1.id, user2_liked_message_ids)
        self.assertNotIn(message2.id, user2_liked_message_ids)

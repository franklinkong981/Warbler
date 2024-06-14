"""User model tests."""

# run these tests like:
#
#    python3 -m unittest test_user_model.py


import os
from unittest import TestCase
from app import create_app

from models import db, connect_db, User, Message, Follows, Likes
from sqlalchemy.exc import IntegrityError

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

        user1 = User.signup(
            email="user1@test.com",
            username="user1",
            password="HASHED_PASSWORD1",
            image_url="www.testurl1.com"
        )

        user2 = User.signup(
            email="user2@test.com",
            username="user2",
            password="HASHED_PASSWORD2",
            image_url="www.testurl2.com"
        )

        user3 = User.signup(
            email="user3@test.com",
            username="user3",
            password="HASHED_PASSWORD3",
            image_url="www.testurl3.com"
        )

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
        self.assertEqual(user1.username, "user1")
        self.assertEqual(user1.email, "user1@test.com")

    def test_repr(self):
        """Does the User model's repr method work as expected?"""
        user1 = User.query.filter(User.username == "user1").first()

        self.assertEqual(repr(user1), f"<User #{user1.id}: {user1.username}, {user1.email}>")

    def test_is_following(self):
        """Does is_following successfully detect when a user is or isn't following another user?"""
        user1 = User.query.filter(User.username == "user1").first()
        user2 = User.query.filter(User.username == "user2").first()
        user3 = User.query.filter(User.username == "user3").first()

        user1.followers.append(user2)
        user2.followers.append(user3)

        self.assertTrue(user2.is_following(user1))
        self.assertTrue(user3.is_following(user2))
        self.assertFalse(user1.is_following(user2))
        self.assertFalse(user2.is_following(user3))
        self.assertFalse(user3.is_following(user1))
        self.assertFalse(user1.is_following(user3))
    
    def test_is_followed_by(self):
        """Does is_followed_by successfully detect when a user is or isn't being followed by another user?"""
        user1 = User.query.filter(User.username == "user1").first()
        user2 = User.query.filter(User.username == "user2").first()
        user3 = User.query.filter(User.username == "user3").first()

        user1.followers.append(user2)
        user2.followers.append(user3)

        self.assertTrue(user1.is_followed_by(user2))
        self.assertTrue(user2.is_followed_by(user3))
        self.assertFalse(user2.is_followed_by(user1))
        self.assertFalse(user3.is_followed_by(user2))
        self.assertFalse(user3.is_followed_by(user1))
        self.assertFalse(user1.is_followed_by(user3))
    
    def test_signup_success(self):
        """Does User.signup successfully create a new user given valid credentials?"""
        user4 = User.signup("user4", "user4@test.com", "HASHED_PASSWORD4", "www.testurl.com")

        self.assertIsNotNone(user4)
        self.assertEqual(user4.username, "user4")
        self.assertEqual(user4.email, "user4@test.com")
        self.assertEqual(user4.image_url, "www.testurl.com")
        db.session.commit()

        users = User.query.all()
        self.assertEqual(len(users), 4)

    def test_signup_fail(self):
        """Does User.signup fail to create a new user if any of the validations like uniqueness, non-nullable fields fail?"""
        # Missing username
        bad_user1 = User.signup(None, "baduser1@test.com", "BAD_PASSWORD1", "www.badurl.com")
        with self.assertRaises(IntegrityError): 
            db.session.commit()
        db.session.rollback()
        # Missing email
        bad_user2 = User.signup("baduser2", None, "BAD_PASSWORD2", "www.badurl.com")
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        # Missing password. This should result in an error inside the User.signup classmethod.
        with self.assertRaises(ValueError):
            User.signup("baduser3", "baduser3@test.com", None, "www.badurl.com")
        # Non-unique username
        bad_user4 = User.signup("user2", "baduser4@test.com", "BAD_PASSWORD4", "www.badurl.com")
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        # Non-unique email
        bad_user5 = User.signup("baduser5", "user3@test.com", "BAD_PASSWORD5", "www.badurl.com")
        with self.assertRaises(IntegrityError):
            db.session.commit()
    
    def test_authenticate_success(self):
        """Does the classmethod User.authenticate successfully return a user when given a valid username and password?"""
        user1 = User.authenticate("user1", "HASHED_PASSWORD1")
        self.assertIsNot(user1, False)
    
    def test_authenticate_fail(self):
        """Does the classmethod User.authenticate fail to return a user when the username or password is invalid?"""
        failed_user1 = User.authenticate("failed_user1", "BAD_PASSWORD1")
        self.assertFalse(failed_user1)
        failed_user2 = User.authenticate("user2", "BAD_PASSWORD2")
        self.assertFalse(failed_user2)
    
    def test_confirm_password(self):
        """Does the classmethod User.confirm_password work as expected?"""
        user1 = User.query.filter(User.username == "user1").first()
        # self.assertTrue(User.confirm_password(user1.id, "HASHED_PASSWORD1"))
        self.assertFalse(User.confirm_password(user1.id, "INVALID_PASSWORD"))

        





        
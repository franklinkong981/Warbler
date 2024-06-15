"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python3 -m unittest test_message_views.py


import os
from unittest import TestCase
from app import create_app, CURR_USER_KEY

from models import db, connect_db, Message, User, Follows, Likes
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

class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()

        self.client = app.test_client()

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

    def test_view_message(self):
        """Can the site visitor view the page for a specific warble?"""

        user1 = User.query.filter(User.username == 'user1').first()
        message1 = Message(
            text="Hi Warbler! This is my first warble!",
            user_id=user1.id
        )
        db.session.add(message1)
        db.session.commit()

        with self.client as c:
            resp = c.get(f"/messages/{message1.id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p class="single-message">Hi Warbler! This is my first warble!</p>', html) 
    
    def test_new_message_page_logged_out(self):
        """Is a user prohibited from seeing the form for creating a new warble when they're logged out?"""

        with self.client as c:
            resp = c.get("/messages/new")
            
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/")
    
    def test_new_message_page_logged_in(self):
        """Is a user allowed to see the page for creating a new warble when they're logged in?"""

        user1 = User.query.filter(User.username == 'user1').first()

        with self.client as c:
            # simulate user1 logging in
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1.id
            resp = c.get("/messages/new")
            html = resp.get_data(as_text=True)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<button class="btn btn-outline-success btn-block">Add my message!</button>', html)

    
    def test_new_message_logged_out(self):
        """Is a user prohibited from creating a new warble when they're logged out?"""

        with self.client as c:
            resp = c.post("/messages/new", data={"text": "This message shouldn't go through!"})
            
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/")
    
    def test_new_message_logged_in(self):
        """Is a user who is logged in allowed to make a new warble for themselves?"""

        user1 = User.query.filter(User.username == 'user1').first()

        with self.client as c:
            # simulate user1 logging in
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1.id
            self.assertEqual(len(user1.messages), 0)
            resp = c.post("/messages/new", data={"text": "user1's first warble!"})

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f"/users/{user1.id}") 
            self.assertEqual(len(user1.messages), 1)
    
    def test_logged_out_like(self):
        """Is a user who is logged out prohibited from liking a warble?"""

        user1 = User.query.filter(User.username == 'user1').first()
        message1 = Message(
            text="Hi Warbler! This is my first warble!",
            user_id=user1.id
        )
        db.session.add(message1)
        db.session.commit()

        with self.client as c:
            resp = c.post(f"/messages/{message1.id}/like")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/")
    
    def test_like_own_warble(self):
        """When a user is signed in, are they prohibited form liking their own warble?"""

        user1 = User.query.filter(User.username == 'user1').first()
        message1 = Message(
            text="Hi Warbler! This is my first warble!",
            user_id=user1.id
        )
        db.session.add(message1)
        db.session.commit()

        with self.client as c:
            # simulate user1 logging in
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1.id
            resp = c.post(f"/messages/{message1.id}/like")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/")
    
    def test_like(self):
        """When a user is signed in, are they allowed to like another user's warble?"""
        user1 = User.query.filter(User.username == 'user1').first()
        user2 = User.query.filter(User.username == 'user2').first()
        message2 = Message(
            text="Hi Warbler! This is my first warble!",
            user_id=user2.id
        )
        db.session.add(message2)
        db.session.commit()

        with self.client as c:
            # simulate user1 logging in
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1.id
            self.assertEqual(len(user1.likes), 0)
            resp = c.post(f"/messages/{message2.id}/like")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(len(user1.likes), 1)
    
    def test_unlike(self):
        """When a user is signed in, are they allowed to unlike another user's warble?"""
        user1 = User.query.filter(User.username == 'user1').first()
        user2 = User.query.filter(User.username == 'user2').first()
        message2 = Message(
            text="Hi Warbler! This is my first warble!",
            user_id=user2.id
        )
        db.session.add(message2)
        db.session.commit()
        user1.likes.append(message2)

        with self.client as c:
            # simulate user1 logging in
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1.id
            self.assertEqual(len(user1.likes), 1)
            resp = c.post(f"/messages/{message2.id}/like")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(len(user1.likes), 0)
    
    def test_delete_message_logged_out(self):
        """When a user is logged out, are they allowed to delete a warble?"""

        user1 = User.query.filter(User.username == 'user1').first()
        message1 = Message(
            text="Hi Warbler! This is my first warble!",
            user_id=user1.id
        )
        db.session.add(message1)
        db.session.commit()

        with self.client as c:
            resp = c.post(f"/messages/{message1.id}/delete")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/")
            # check to make sure message1 still exists and wasn't deleted
            msg = Message.query.all()
            self.assertEqual(len(msg), 1)
    
    def test_delete_own_message(self):
        """When a user is logged in, are they allowed to delete their own warble?"""

        user1 = User.query.filter(User.username == 'user1').first()
        message1 = Message(
            text="Hi Warbler! This is my first warble!",
            user_id=user1.id
        )
        db.session.add(message1)
        db.session.commit()

        with self.client as c:
            # simulate user1 logging in
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1.id
            msg = Message.query.all()
            self.assertEqual(len(msg), 1)
            resp = c.post(f"/messages/{message1.id}/delete")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f"/users/{user1.id}")
            # check to make sure message1 was deleted
            msg = Message.query.all()
            self.assertEqual(len(msg), 0)
    
    def test_delete_other_message(self):
        """When a user is logged in, are they prohibited from deleting the message of another user?"""

        user1 = User.query.filter(User.username == 'user1').first()
        user2 = User.query.filter(User.username == 'user2').first()
        message2 = Message(
            text="Hi Warbler! This is my first warble!",
            user_id=user2.id
        )
        db.session.add(message2)
        db.session.commit()

        with self.client as c:
            # simulate user1 logging in
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1.id
            msg = Message.query.all()
            self.assertEqual(len(msg), 1)
            resp = c.post(f"/messages/{message2.id}/delete")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/")
            # check to make sure message2 was deleted
            msg = Message.query.all()
            self.assertEqual(len(msg), 1)










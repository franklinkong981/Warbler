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
    
    def test_logged_out_signup(self):
        """Can a logged out user see the sign-up page?"""

        with self.client as c:
            resp = c.get("/signup")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h2 class="join-message">Join Warbler today.</h2>', html)
    
    def test_logged_in_signup(self):
        """When a logged in user tries to access the sign-up page, are they redirected to the home page?"""

        user1 = User.query.filter(User.username == 'user1').first()

        with self.client as c:
            # simulate user1 logging in
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1.id
            
            resp = c.get("/signup")
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/")
    
    def test_signup_user(self):
        """Can a new user sign up and create an account?"""
        with self.client as c:
            resp = c.post("/signup", data={"username": "user4", "email": "user4@test.com", "password": "HASHED_PASSWORD4", "image_url": "www.testurl4.com"})
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/")
            # Is the new user added to the database?
            all_users = User.query.all()
            self.assertEqual(len(all_users), 4)
    
    def test_logged_out_login(self):
        """Can a logged out user see the login page?"""

        with self.client as c:
            resp = c.get("/login")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h2 class="join-message">Welcome back.</h2>', html) 
    
    def test_logged_in_login(self):
        """When a logged in user tries to access the login page, are they redirected to the home page?"""

        user1 = User.query.filter(User.username == 'user1').first()

        with self.client as c:
            # simulate user1 logging in
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1.id
            
            resp = c.get("/login")
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/")
    
    def test_login_user(self):
        """Can a user successfully log in?"""

        user1 = User.query.filter(User.username == 'user1').first()

        with self.client as c:
            resp = c.post("/login", data={"username": "user1", "password": "HASHED_PASSWORD1"})
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/")
            # Is the logged in user's id added to the session?
            with c.session_transaction() as sess:
                self.assertEqual(sess[CURR_USER_KEY], user1.id)
    
    def test_user_search(self):
        """If a site visitor searches with the term 'user', do they see the appropriate matches?"""
        with self.client as c:
            c.post("/signup", data={"username": "iwontshowup", "email": "user4@test.com", "password": "HASHED_PASSWORD4", "image_url": "www.testurl4.com"})
            resp = c.get("/users?q=user")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>@user1</p>', html)
            self.assertIn('<p>@user2</p>', html)
            self.assertIn('<p>@user3</p>', html)
            self.assertNotIn('<p>@iwontshowup</p>', html)
    
    def test_user_profile(self):
        """If a logged in user visits their profile, do they have options to edit their profile and delete their account?"""

        user1 = User.query.filter(User.username == 'user1').first()

        with self.client as c:
            # simulate user1 logging in
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1.id
            resp = c.get(f"/users/{user1.id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<a href="/users/profile" class="btn btn-outline-secondary">Edit Profile</a>', html)
            self.assertIn('<button class="btn btn-outline-danger ml-2">Delete Profile</button>', html)
    
    def test_logged_out_user1_following(self):
        """If a user is logged out and tries to access user 1's following, do they get redirected to the home page?"""

        user1 = User.query.filter(User.username == 'user1').first()

        with self.client as c:
            resp = c.get(f"/users/{user1.id}/following")
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/")
    
    def test_logged_in_user1_following(self):
        """If user2 is logged in, are they able to access user 1's following page?"""

        user1 = User.query.filter(User.username == 'user1').first()
        user2 = User.query.filter(User.username == 'user2').first()

        with self.client as c:
            # simulate user2 logging in
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user2.id
            resp = c.get(f"/users/{user1.id}/following")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
    
    def test_logged_out_user1_followers(self):
        """If a user is logged out and tries to access user 1's followers, do they get redirected to the home page?"""

        user1 = User.query.filter(User.username == 'user1').first()

        with self.client as c:
            resp = c.get(f"/users/{user1.id}/followers")
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/")
    
    def test_logged_in_user1_followers(self):
        """If user2 is logged in, are they able to access user 1's followers page?"""

        user1 = User.query.filter(User.username == 'user1').first()
        user2 = User.query.filter(User.username == 'user2').first()

        with self.client as c:
            # simulate user2 logging in
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user2.id
            resp = c.get(f"/users/{user1.id}/followers")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
    
    def test_logged_out_follow(self):
        """If a user is logged out, are they prohibited from following another user?"""

        user2 = User.query.filter(User.username == 'user2').first()

        with self.client as c:
            resp = c.post(f'/users/follow/{user2.id}')
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/")

            # make sure the follow wasn't successful
            self.assertEqual(len(user2.followers), 0)
    
    def test_logged_in_follow(self):
        """If a user is logged in, are they able to follow another user?"""

        user1 = User.query.filter(User.username == 'user1').first()
        user2 = User.query.filter(User.username == 'user2').first()

        with self.client as c:
            # simulate user1 logging in
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1.id
            resp = c.post(f"/users/follow/{user2.id}")
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f"/users/{user1.id}/following")

            self.assertEqual(len(user1.following), 1)
            self.assertEqual(len(user2.followers), 1)
    
    def test_logged_out_stop_following(self):
        """If a user is logged out, are they prohibited from stop following someone?"""

        user1 = User.query.filter(User.username == 'user1').first()
        user2 = User.query.filter(User.username == 'user2').first()
        user2.followers.append(user1)

        with self.client as c:
            resp = c.post(f'/users/stop-following/{user2.id}')
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/")

            # make sure the stop-follow wasn't successful
            self.assertEqual(len(user2.followers), 1)
    
    def test_logged_in_stop_following(self):
        """If a user is logged in, are they able to stop following another user?"""

        user1 = User.query.filter(User.username == 'user1').first()
        user2 = User.query.filter(User.username == 'user2').first()
        user2.followers.append(user1)

        with self.client as c:
            # simulate user1 logging in
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1.id
            self.assertEqual(len(user2.followers), 1)
            resp = c.post(f"/users/stop-following/{user2.id}")
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f"/users/{user1.id}/following")

            self.assertEqual(len(user2.followers), 0)
    
    def test_logged_out_likes(self):
        """If a user is signed out, are they prohibited from seeing a user's likes?"""

        user1 = User.query.filter(User.username == 'user1').first()

        with self.client as c:
            resp = c.get(f'/users/{user1.id}/likes')
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/")

    def test_logged_in_likes(self):
        """If a user is logged in, are they able to see another user's likes?"""

        user1 = User.query.filter(User.username == 'user1').first()
        user2 = User.query.filter(User.username == 'user2').first()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1.id
            resp = c.get(f"/users/{user1.id}/followers")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
    
    def test_logged_out_edit_profile(self):
        """If a user is logged out, are they prohibited from seeing the edit profile form?"""

        with self.client as c:
            resp = c.get("/users/profile")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/")
    
    def test_logged_in_edit_profile(self):
        """If a user is logged in, are they able to see the edit profile form?"""

        user1 = User.query.filter(User.username == 'user1').first()

        with self.client as c:
            # simulate user1 logging in
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1.id
            
            resp = c.get("/users/profile")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h2 class="join-message">Edit Your Profile.</h2>', html)
    
    def test_edit_profile(self):
        """If a user is logged in, are they able to successfully update their profile information?"""

        user1 = User.query.filter(User.username == 'user1').first()

        with self.client as c:
            # simulate user1 logging in
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1.id
            resp = c.post("/users/profile", data={"username": "user_new", "email": "usernew@test.com", "password": "HASHED_PASSWORD1"})

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f"/users/{user1.id}")
            self.assertEqual(user1.username, "user_new")
            self.assertEqual(user1.email, "usernew@test.com")
    
    def test_logged_out_delete_account(self):
        """If a user is already logged out, are they prohibited from deleting their account?"""

        with self.client as c:
            resp = c.post("/users/delete")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, '/')

    def test_logged_in_delete_account(self):
        """If a user is logged in, are they allowed to delete their account?"""

        user1 = User.query.filter(User.username == 'user1').first()

        with self.client as c:
            # simulate user1 logging in
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user1.id
            current_users = User.query.all()
            self.assertEqual(len(current_users), 3)

            resp = c.post("/users/delete")

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/signup")
            new_users = User.query.all()
            self.assertEqual(len(new_users), 2)

            



            



    
    

    



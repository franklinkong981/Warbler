import os

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, LoginForm, MessageForm, EditProfileForm
from models import db, connect_db, User, Message, Likes, Follows

CURR_USER_KEY = "curr_user"

def create_app(db_name, testing=False):
    """Create an instance of the app so I can have a production database and a separate testing database."""
    app = Flask(__name__)
    app.testing = testing
    # Get DB_URI from environ variable (useful for production/testing) or,
    # if not set there, use development local db.
    app.config['SQLALCHEMY_DATABASE_URI'] = (os.environ.get('DATABASE_URL', f'postgresql:///{db_name}'))
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
    app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
    toolbar = DebugToolbarExtension(app)
    if app.testing:
        app.config['SQLALCHEMY_ECHO'] = False
        app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']
        app.config['WTF_CSRF_ENABLED'] = False
    else:
        app.config['SQLALCHEMY_ECHO'] = True
    
    #Routes and view functions for the application.

    ##############################################################################
    # User signup/login/logout


    @app.before_request
    def add_user_to_g():
        """If we're logged in, add curr user to Flask global."""

        if CURR_USER_KEY in session:
            g.user = User.query.get(session[CURR_USER_KEY])

        else:
            g.user = None


    def do_login(user):
        """Log in user."""

        session[CURR_USER_KEY] = user.id


    def do_logout():
        """Logout user."""

        if CURR_USER_KEY in session:
            del session[CURR_USER_KEY]


    @app.route('/signup', methods=["GET", "POST"])
    def signup():
        """Handle user signup.

        If user is already signed in, redirect to home page.

        Create new user and add to DB. Redirect to home page.

        If form not valid, present form.

        If the there already is a user with that username: flash message
        and re-present form.
        """

        if g.user:
            flash("You already have an account and are signed in.", "danger")
            return redirect("/")

        form = UserAddForm()

        if form.validate_on_submit():
            try:
                user = User.signup(
                    username=form.username.data,
                    password=form.password.data,
                    email=form.email.data,
                    image_url=form.image_url.data or User.image_url.default.arg,
                )
                db.session.commit()

            except IntegrityError:
                flash("Username and/or email already taken", 'danger')
                return render_template('users/signup.html', form=form)

            do_login(user)

            return redirect("/")

        else:
            return render_template('users/signup.html', form=form)


    @app.route('/login', methods=["GET", "POST"])
    def login():
        """Handle user login. If user is already signed in, redirect to home page."""

        if g.user:
            flash("You are already logged in.", "danger")
            return redirect("/")

        form = LoginForm()

        if form.validate_on_submit():
            user = User.authenticate(form.username.data,
                                    form.password.data)

            if user:
                do_login(user)
                flash(f"Hello, {user.username}!", "success")
                return redirect("/")

            flash("Invalid credentials.", 'danger')

        return render_template('users/login.html', form=form)


    @app.route('/logout')
    def logout():
        """Handle logout of user."""

        if not g.user:
            flash("You weren't signed in to begin with!.", "danger")
            return redirect("/")

        do_logout()
        flash("Successfully logged out.", "success")
        return redirect("/")    


    ##############################################################################
    # General user routes:

    @app.route('/users')
    def list_users():
        """Page with listing of users.

        Can take a 'q' param in querystring to search by that username.
        """

        search = request.args.get('q')

        if not search:
            users = User.query.all()
        else:
            users = User.query.filter(User.username.like(f"%{search}%")).all()

        return render_template('users/index.html', users=users)


    @app.route('/users/<int:user_id>')
    def users_show(user_id):
        """Show user profile."""

        user = User.query.get_or_404(user_id)

        # snagging messages in order from the database;
        # user.messages won't be in order by default
        messages = (Message
                    .query
                    .filter(Message.user_id == user_id)
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())
        return render_template('users/show.html', user=user, messages=messages, likes=user.likes)


    @app.route('/users/<int:user_id>/following')
    def show_following(user_id):
        """Show list of people this user is following."""

        if not g.user:
            flash("Sign in to see a user's following.", "danger")
            return redirect("/")

        user = User.query.get_or_404(user_id)
        return render_template('users/following.html', user=user)


    @app.route('/users/<int:user_id>/followers')
    def users_followers(user_id):
        """Show list of followers of this user."""

        if not g.user:
            flash("Sign in to see a user's followers.", "danger")
            return redirect("/")

        user = User.query.get_or_404(user_id)
        return render_template('users/followers.html', user=user)


    @app.route('/users/follow/<int:follow_id>', methods=['POST'])
    def add_follow(follow_id):
        """Add a follow for the currently-logged-in user."""

        if not g.user:
            flash("Sign in to follow someone.", "danger")
            return redirect("/")

        followed_user = User.query.get_or_404(follow_id)
        g.user.following.append(followed_user)
        db.session.commit()

        return redirect(f"/users/{g.user.id}/following")


    @app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
    def stop_following(follow_id):
        """Have currently-logged-in-user stop following this user."""

        if not g.user:
            flash("Sign in to stop following someone.", "danger")
            return redirect("/")
        
        # list of ids of users that the logged in user currently follows
        following_ids = [user.id for user in g.user.following]
        # check to make sure currently logged in user is currently following the user they want to stop following
        if follow_id not in following_ids:
            flash("You are already not following this user", "danger")
            return redirect(f"/users/{g.user.id}/following")

        followed_user = User.query.get(follow_id)
        g.user.following.remove(followed_user)
        db.session.commit()

        return redirect(f"/users/{g.user.id}/following")

    @app.route('/users/<int:user_id>/likes')
    def view_likes(user_id):
        """Displays all the warbles/messages that are currently liked by the user with id of user_id."""

        if not g.user:
            flash("Sign in to see a user's liked warbles.", "danger")
            return redirect("/")

        user = User.query.get_or_404(user_id)
        return render_template('users/likes.html', user=user, likes=user.likes)


    @app.route('/users/profile', methods=["GET", "POST"])
    def profile():
        """Show form to update user profile information, update profile for current userif password in form matches."""

        if not g.user:
            flash("Sign in to update your profile information", "danger")
            return redirect("/")
        
        form = EditProfileForm(obj=g.user)
        if form.validate_on_submit():
            # Need to make sure password matches, then need to make sure the username is STILL unique.
            if User.confirm_password(session[CURR_USER_KEY], form.password.data):
                g.user.username = form.username.data
                g.user.email = form.email.data
                g.user.image_url = form.image_url.data or User.image_url.default.arg
                g.user.header_image_url = form.header_image_url.data or User.header_image_url.default.arg
                g.user.bio = form.bio.data or None
                g.user.location = form.location.data or None

                try:
                    db.session.commit()
                except IntegrityError:
                    flash("Unable to update profile, new username/email already taken", 'danger')
                    return redirect('/')
                
                flash("Profile successfully updated!", "success")
                return redirect(f'/users/{session[CURR_USER_KEY]}')
            else:
                flash("Unable to update profile. Invalid password.", "danger")
                return redirect('/')

        return render_template("users/edit.html", form=form, user_id=g.user.id)


    @app.route('/users/delete', methods=["POST"])
    def delete_user():
        """Delete user."""

        if not g.user:
            flash("Sign in to delete your account.", "danger")
            return redirect("/")

        do_logout()

        db.session.delete(g.user)
        db.session.commit()

        return redirect("/signup")


    ##############################################################################
    # Messages routes:

    @app.route('/messages/new', methods=["GET", "POST"])
    def messages_add():
        """Add a message:

        Show form if GET. If valid, update message and redirect to user page.
        """

        if not g.user:
            flash("Sign in to create a new warble.", "danger")
            return redirect("/")

        form = MessageForm()

        if form.validate_on_submit():
            msg = Message(text=form.text.data)
            g.user.messages.append(msg)
            db.session.commit()

            return redirect(f"/users/{g.user.id}")

        return render_template('messages/new.html', form=form)


    @app.route('/messages/<int:message_id>', methods=["GET"])
    def messages_show(message_id):
        """Show a message."""

        msg = Message.query.get_or_404(message_id)
        return render_template('messages/show.html', message=msg)

    @app.route('/messages/<int:message_id>/like', methods=["POST"])
    def toggle_like(message_id):
        """Toggles the logged in user liking/unliking a specific message. The logged in user can only like/unlike messages made by 
        other users. If user likes a message, the Like is added to the database. If the user unlikes a message, the Like is removed from
        the database."""

        if not g.user:
            flash("Sign in to like a warble.", "danger")
            return redirect("/")

        msg = Message.query.get_or_404(message_id)

        # Logged in user can't like their own warbles.
        if msg.user_id == session[CURR_USER_KEY]:
            flash("You can't like a warble you created!")
            return redirect("/")

        if msg in g.user.likes:
            # If the message is contained within logged in user's likes, then the user has just unliked it.
            g.user.likes = [like for like in g.user.likes if like != msg]
            flash("Warble successfully unliked!", "success")
        else:
            # If the message isn't contained within logged in user's likes, then the user has just liked it.
            g.user.likes.append(msg)
            flash("Warble successfully liked!", "success")

        db.session.commit()

        
        redirect_url = request.referrer or "/"
        return redirect(redirect_url)



    @app.route('/messages/<int:message_id>/delete', methods=["POST"])
    def messages_destroy(message_id):
        """Delete a message. A user must be logged in to delete a message, and  logged in users can only delete their own messages."""

        if not g.user:
            flash("Sign in to delete a warble.", "danger")
            return redirect("/")

        msg = Message.query.get_or_404(message_id)

        if msg.user.id != session[CURR_USER_KEY]:
            flash("You can only delete a warble that you've created.", "danger")
            return redirect("/")
        
        db.session.delete(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")


    ##############################################################################
    # Homepage and error pages


    @app.route('/')
    def homepage():
        """Show homepage:

        - anon users: no messages
        - logged in: 100 most recent messages of followed_users
        """

        if g.user:
            # messages displayed in home page should either belong to the logged in user or a user that the logged in user follows.
            matching_user_ids = [user.id for user in g.user.following] + [g.user.id]
            messages = (Message
                        .query
                        .filter(Message.user_id.in_(matching_user_ids))
                        .order_by(Message.timestamp.desc())
                        .limit(100)
                        .all())
            print("The length is ", len(messages))

            return render_template('home.html', messages=messages, likes=g.user.likes)

        else:
            return render_template('home-anon.html')
    
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html")


    ##############################################################################
    # Turn off all caching in Flask
    #   (useful for dev; in production, this kind of stuff is typically
    #   handled elsewhere)
    #
    # https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

    @app.after_request
    def add_header(req):
        """Add non-caching headers on every request."""

        req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        req.headers["Pragma"] = "no-cache"
        req.headers["Expires"] = "0"
        req.headers['Cache-Control'] = 'public, max-age=0'
        return req
    
    return app

if __name__ == '__main__':
    app = create_app('warbler')
    connect_db(app)
    app.run(debug=True)




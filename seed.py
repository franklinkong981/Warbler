"""Seed database with sample data from CSV Files."""

import os
from csv import DictReader
from app import db
from models import User, Message, Follows, Likes, db, connect_db
from app import app
from dotenv import load_dotenv

load_dotenv()
# app = create_app('warbler')
print("The database is: ", os.environ.get('DATABASE_URL'))
connect_db(app)
app.app_context().push()

# Create all tables
db.drop_all()
db.create_all()

# If tables aren't empty, empty them
User.query.delete()
Message.query.delete()
Follows.query.delete()
Likes.query.delete()

with open('generator/users.csv') as users:
    db.session.bulk_insert_mappings(User, DictReader(users))

with open('generator/messages.csv') as messages:
    db.session.bulk_insert_mappings(Message, DictReader(messages))

with open('generator/follows.csv') as follows:
    db.session.bulk_insert_mappings(Follows, DictReader(follows))

db.session.commit()

# ruff: noqa: E402
# ruff: noqa: F403
import os
from flask import Flask
from models import db, Teacher
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

app = Flask(__name__)
# app.config.from_object(Config)
# Load environment variables
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
# PostgreSQL connection string format
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.environ.get('SQLALCHEMY_TRACK_MODIFICATIONS')

# app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
# app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS', False)

db.init_app(app)
bcrypt = Bcrypt(app)

def check_and_insert_teacher():
    """Check if a teacher exists and insert if not."""
    # Teacher details
    name = 'Arijit De'
    email = 'arijitde2050@gmail.com'
    password = 'abcd1234'

    # Check if the teacher already exists in the database by email
    existing_teacher = Teacher.query.filter_by(email=email).first()

    if not existing_teacher:
        # Hash the password with bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Create a new teacher object
        new_teacher = Teacher(name=name, email=email, password=hashed_password)

        # Add to the database and commit the transaction
        db.session.add(new_teacher)
        db.session.commit()
        print(f"New teacher {name} inserted successfully!")


# Ensure this code runs when the app starts
@app.before_request
def startup():
    with app.app_context():
        check_and_insert_teacher()

from routes import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6500)
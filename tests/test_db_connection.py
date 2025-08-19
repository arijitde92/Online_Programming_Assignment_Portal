import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sqlalchemy import text
from src.models import db
from flask import Flask
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

# Load the .env file
load_dotenv("src/.env")

app = Flask(__name__)

# Load environment variables
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
# PostgreSQL connection string format
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.environ.get('SQLALCHEMY_TRACK_MODIFICATIONS')

db.init_app(app)
bcrypt = Bcrypt(app)

def test_db_connection():
    """Test database connection."""
    with app.app_context():
        try:
            # Try a simple query
            db.session.execute(text('SELECT 1'))
        except Exception as e:
            assert False, f"Database connection failed: {e}"

if __name__ == "__main__":
    test_db_connection()
    print("Database connection successful.")
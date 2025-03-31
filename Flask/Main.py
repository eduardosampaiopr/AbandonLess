from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv()  # Carrega as variáveis do .env

DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")


app = Flask(__name__)
app.secret_key = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL

db = SQLAlchemy(app)

with app.app_context():
    db.create_all()

from Routes import *

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)

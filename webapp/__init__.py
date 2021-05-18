import corha
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)

app.root = os.getcwd()
app.envs = corha.credentials_loader(app.root + "\\.env")

app.config['SQLALCHEMY_DATABASE_URI'] = app.envs.postgresql
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SECRET_KEY'] = app.envs.secret_key

login_manager = LoginManager()
login_manager.init_app(app)

db = SQLAlchemy(app)

# from webapp import models
# db.create_all()

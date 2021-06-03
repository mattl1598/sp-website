import corha
import os
import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import markdown
from flask_socketio import SocketIO
from flask_navigation import Navigation

app = Flask(__name__)

app.root = os.getcwd()
app.envs = corha.credentials_loader(app.root + "\\.env")

app.static_content_cache = {"js": {}, "css": {}}

app.config['SQLALCHEMY_DATABASE_URI'] = app.envs.postgresql
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SECRET_KEY'] = app.envs.secret_key

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

nav = Navigation()
nav.init_app(app)

db = SQLAlchemy(app)

# initialise socketio plugin
socketio = SocketIO(app)


def svg(filename):
	"""
	function for loading basic svg icons as paths in html template
	without needing an extra http request

	:authors:
		- Matt
	:param filename: string
	:return: string containing html path element
	"""
	try:
		path = {
			"home": '<path d="M4 0l-4 3h1v4h2v-2h2v2h2v-4.03l1 .03-4-3z" />',
			"logout": '<path d="M3 0v1h4v5h-4v1h5v-7h-5zm-1 2l-2 1.5 2 1.5v-1h4v-1h-4v-1z" />',
			"double-chevrons": '<path d="M 1 1 l 6.5 7 l -6.5 7" class="dc"/> \n\t <path d="M 7 1 l 6.5 7 l -6.5 7" class="dc"/>',
			"map": '<path d="M0 0v8h8v-2.38a.5.5 0 0 0 0-.22v-5.41h-8zm1 1h6v4h-1.5a.5.5 0 0 0-.09 0 .5.5 0 1 0 .09 1h1.5v1h-6v-6zm2.5 1c-.83 0-1.5.67-1.5 1.5 0 1 1.5 2.5 1.5 2.5s1.5-1.5 1.5-2.5c0-.83-.67-1.5-1.5-1.5zm0 1c.28 0 .5.22.5.5s-.22.5-.5.5-.5-.22-.5-.5.22-.5.5-.5z"/>',
			"globe": '<path d="M4 0c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm0 1c.33 0 .64.09.94.19-.21.2-.45.38-.41.56.04.18.69.13.69.5 0 .27-.42.35-.13.66.35.35-.64.98-.66 1.44-.03.83.84.97 1.53.97.42 0 .53.2.5.44-.54.77-1.46 1.25-2.47 1.25-.38 0-.73-.09-1.06-.22.22-.44-.28-1.31-.75-1.59-.23-.23-.72-.14-1-.25-.09-.27-.18-.54-.19-.84.03-.05.08-.09.16-.09.19 0 .45.38.59.34.18-.04-.74-1.31-.31-1.56.2-.12.6.39.47-.16-.12-.51.36-.28.66-.41.26-.11.45-.41.13-.59-.06-.03-.13-.1-.22-.19.45-.27.97-.44 1.53-.44zm2.31 1.09c.18.22.32.46.44.72 0 .01 0 .02 0 .03-.04.07-.11.11-.22.22-.28.28-.32-.21-.44-.31-.13-.12-.6.02-.66-.13-.07-.18.5-.42.88-.53z"/>',
			"graph": '<path d="M.97 0l3.03 3 1-1 3 3.03-1 1-2-2.03-1 1-4-4 .97-1zm7.03 7v1h-8v-1h8z"/>',
			"eye": '<path d="M4.03 0c-2.53 0-4.03 3-4.03 3s1.5 3 4.03 3c2.47 0 3.97-3 3.97-3s-1.5-3-3.97-3zm-.03 1c1.11 0 2 .9 2 2 0 1.11-.89 2-2 2-1.1 0-2-.89-2-2 0-1.1.9-2 2-2zm0 1c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1c0-.1-.04-.19-.06-.28-.08.16-.24.28-.44.28-.28 0-.5-.22-.5-.5 0-.2.12-.36.28-.44-.09-.03-.18-.06-.28-.06z" transform="translate(0 1)"/>',
			"x": '<path d="m 2 2 l 16 16 m -16 0 l 16 -16" />'
		}[filename]
	except KeyError:
		path = '<path d="M4 0l-4 3h1v4h2v-2h2v2h2v-4.03l1 .03-4-3z" />'
	return path


def format_date(input, format):
	dt = datetime.datetime.strptime(input, "%Y-%m-%d %H:%M:%S.%f")
	return dt.strftime(format)


app.jinja_env.globals.update(
	format_date=format_date,
	md=markdown.markdown,
	svg=svg
)

# from webapp import models
# db.create_all()

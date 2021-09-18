import secrets

import corha
import os
import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import markdown
from flask_socketio import SocketIO
from flask_navigation import Navigation
from os import walk
from scss.compiler import Compiler

app = Flask(__name__)

app.root = os.getcwd().replace("\\", "/")
print(app.root)
app.envs = corha.credentials_loader(app.root + "/.env")

app.static_content_cache = {"js": {}, "css": {}}

# get available sounds
app.sounds_path = "static/sounds/"
for (_, _, app.available_sounds) in walk("webapp/" + app.sounds_path):
	print(app.available_sounds)
	break

# # get available css files
# app.css_path = "static/css/"
# for (_, _, app.available_css) in walk("webapp/" + app.css_path):
# 	print(app.available_css)
# 	break

# get available scss files
app.scss_path = "static/scss/"
for (_, _, app.available_scss) in walk("webapp/" + app.scss_path):
	print(app.available_scss)
	break

scss_paths = [
	"webapp/" + app.scss_path,
	"webapp/" + app.scss_path + "partials"
]
app.scss_compiler = Compiler(search_path=scss_paths)

for file in app.available_scss:
	with open(str(app.root + "/webapp/static/scss/" + file), "r") as contents:
		app.static_content_cache["css"][file[:-5]+".css"] = app.scss_compiler.compile_string(contents.read())

app.config['SQLALCHEMY_DATABASE_URI'] = app.envs.postgresql
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SECRET_KEY'] = app.envs.secret_key
app.config['FLASK_ENV'] = "development"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

nav = Navigation()
nav.init_app(app)

db = SQLAlchemy(app)

# initialise socketio plugin
socketio = SocketIO(app)


def debug(string):
	print(app.config.get("FLASK_ENV"))
	if app.config.get("FLASK_ENV") == "development":
		print(string)


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
			"x": '<path d="m 2 2 l 16 16 m -16 0 l 16 -16" />',
			"link": '<path d="M5.88.03c-.18.01-.36.03-.53.09-.27.1-.53.25-.75.47a.5.5 0 1 0 .69.69c.11-.11.24-.17.38-.22.35-.12.78-.07 1.06.22.39.39.39 1.04 0 1.44l-1.5 1.5c-.44.44-.8.48-1.06.47-.26-.01-.41-.13-.41-.13a.5.5 0 1 0-.5.88s.34.22.84.25c.5.03 1.2-.16 1.81-.78l1.5-1.5c.78-.78.78-2.04 0-2.81-.28-.28-.61-.45-.97-.53-.18-.04-.38-.04-.56-.03zm-2 2.31c-.5-.02-1.19.15-1.78.75l-1.5 1.5c-.78.78-.78 2.04 0 2.81.56.56 1.36.72 2.06.47.27-.1.53-.25.75-.47a.5.5 0 1 0-.69-.69c-.11.11-.24.17-.38.22-.35.12-.78.07-1.06-.22-.39-.39-.39-1.04 0-1.44l1.5-1.5c.4-.4.75-.45 1.03-.44.28.01.47.09.47.09a.5.5 0 1 0 .44-.88s-.34-.2-.84-.22z" />',
			"code": '<path d="M5 0l-3 6h1l3-6h-1zm-4 1l-1 2 1 2h1l-1-2 1-2h-1zm5 0l1 2-1 2h1l1-2-1-2h-1z"/>',
			"bin": '<path d="M3 0c-.55 0-1 .45-1 1h-1c-.55 0-1 .45-1 1h7c0-.55-.45-1-1-1h-1c0-.55-.45-1-1-1h-1zm-2 3v4.81c0 .11.08.19.19.19h4.63c.11 0 .19-.08.19-.19v-4.81h-1v3.5c0 .28-.22.5-.5.5s-.5-.22-.5-.5v-3.5h-1v3.5c0 .28-.22.5-.5.5s-.5-.22-.5-.5v-3.5h-1z"/>'
		}[filename]
	except KeyError:
		path = '<path d="M4 0l-4 3h1v4h2v-2h2v2h2v-4.03l1 .03-4-3z" />'
	return path


def format_date(input, format):
	dt = datetime.datetime.strptime(input, "%Y-%m-%d %H:%M:%S.%f")
	return dt.strftime(format)


def key_64(char_len):
	nbytes = round(char_len / 1.34375)
	return str(secrets.token_urlsafe(nbytes))


app.jinja_env.globals.update(
	format_date=format_date,
	md=markdown.markdown,
	svg=svg,
	len=len,
	range=range
)

from webapp import models
db.create_all()

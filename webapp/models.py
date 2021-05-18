from datetime import datetime
from webapp import db
from webapp import login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(db.Model, UserMixin):
	id = db.Column(db.String(16), primary_key=True)
	username = db.Column(db.String(15), unique=True)
	firstname = db.Column(db.String(20))
	lastname = db.Column(db.String(30))
	email = db.Column(db.String(120), unique=True)
	role = db.Column(db.String(40), nullable=False)
	password_hash = db.Column(db.String(128))
	password = db.Column(db.String(60))
	active_features = db.Column(db.PickleType, nullable=False, default=[])
	homepage_order = db.Column(db.PickleType, nullable=False, default={})
	# sp_post = db.relationship('SPPost', backref='spuser', lazy=True)

	def __repr__(self):
		return f"User('{self.id}', '{self.firstname}', '{self.lastname}', '{self.username}', '{self.role}', '{self.email}')"

	@property
	def password(self):
		raise AttributeError('password is not a readable attribute')

	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)

	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)


class SPPost(db.Model):
	id = db.Column(db.String(16), primary_key=True)
	date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
	title = db.Column(db.Text, nullable=False)
	category = db.Column(db.Text, nullable=False)
	content = db.Column(db.Text, nullable=False)
	author = db.Column(db.String(40))

	def __repr__(self):
		return f"SPPost('{self.id}', '{self.date}', '{self.title}', '{self.category}', '{self.content}', '{self.author}')"

	def get_dict(self):
		post_dict = {
			"id": self.id,
			"date": self.date,
			"title": self.title,
			"category": self.category,
			"content": self.content,
			"author": self.author
		}
		return post_dict


@login_manager.user_loader
def load_user(user_id):
	return User.query.get(str(user_id))


class Invite(db.Model):
	id = db.Column(db.String(16), primary_key=True)
	valid = db.Column(db.Boolean)
	role = db.Column(db.String(40), nullable=False)
	active_features = db.Column(db.PickleType, nullable=False, default=[])
	homepage_order = db.Column(db.PickleType, nullable=False, default={})

	def __repr__(self):
		return f"Invite('{self.id}', '{self.valid}', '{self.role}', '{self.active_features}','{self.homepage_order}')"

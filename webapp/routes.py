import json
from pprint import pprint
import corha.corha as corha
import dotmap
from webapp import app, db, socketio, debug, key_64
from flask import request, make_response, abort, render_template, redirect, url_for, session, send_file, \
	send_from_directory
from flask_login import login_user, logout_user, current_user, login_required
from webapp.forms import LoginForm, Register, InviteForm, FeedbackForm
from webapp.models import User, Invite, BlogPost, BlogImage, Feedback, Show, RadioPlayViewCounts as RPVC
from datetime import datetime
from flask_socketio import emit, join_room
from webapp.navbar import gen_nav
import mammoth
from PIL import Image
import io


@app.before_request
def before_request():
	session.permanent = True
	if current_user.is_authenticated:
		gen_nav()


@app.get("/sounds/<filename>")
def sound(filename):
	print(filename)
	if filename not in app.available_sounds:
		debug("not found")
		abort(404)
	else:
		debug("found")
		response = send_from_directory(app.sounds_path, filename)
		return response


@app.post("/sounds_counter")
def sounds_counter():
	listen_ids = RPVC.query.with_entities(RPVC.id).all()
	new_id = key_64(16)
	while (new_id,) in listen_ids:
		new_id = key_64(16)

	new_listen = RPVC(
		id=new_id,
		show_id=request.json["show_id"],
		timestamp=datetime.utcnow(),
		ip_address=request.headers.get('CF-Connecting-IP'),
		user_agent=request.json["user_agent"],
		increment_value=1
	)

	db.session.add(new_listen)
	db.session.commit()

	return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}



@login_required
@app.route("/feedback", methods=["GET", "POST"])
def feedback():
	referrer_endpoint = "/" + request.referrer.replace(request.url_root, "")
	form = FeedbackForm()
	if request.method == "POST":
		now = datetime.utcnow()
		used_ids = [value[0] for value in Feedback.query.with_entities(Feedback.id).all()]
		new_issue = Feedback(
			id=corha.rand_string(str(now), 16, used_ids),
			referrer=form.referrer_page.data,
			subject=form.subject.data,
			body=form.issue_body.data,
			author=current_user.id
		)
		db.session.add(new_issue)
		db.session.commit()
		return redirect(form.referrer_page.data)
	else:
		form.referrer_page.data = referrer_endpoint
		return render_template(
			"feedback.html",
			form=form,
			ref_end=referrer_endpoint,
			css="feedback.css", js=[]
		)


@login_required
@app.route("/admin", methods=["GET", "POST"])
def admin():
	invite_form = InviteForm()
	if request.method == "POST":
		validation = True
		# check if email has been used before
		used_emails = [value[0] for value in User.query.with_entities(User.email).all()]
		validation = False if invite_form.invite_email.data in used_emails else validation
		invite_ids = [value[0] for value in Invite.query.with_entities(Invite.id).all()]
		if validation:
			user_ids = [value[0] for value in User.query.with_entities(User.id).all()]
			user_id = corha.rand_string(invite_form.invite_email.data, 16, user_ids)
			invite_kwargs = {
				"id": corha.rand_string(str(datetime.utcnow()), 16, invite_ids),
				"valid": True,
				"role": "author",
				"place_holder": user_id if invite_form.invite_make_placeholder.data else "",
				"active_features": ["manage_blog"],
				"homepage_order": {}
			}
			new_invite = Invite(**invite_kwargs)
			db.session.add(new_invite)
			if invite_form.invite_make_placeholder.data:
				user_kwargs = {
					"id": user_id,
					"username": user_id,
					"firstname": str(invite_form.invite_firstname.data),
					"lastname": str(invite_form.invite_lastname.data),
					"email": str(invite_form.invite_email.data),
					"password": "",
					"role": "author",  # invite_form.role,
					"active_features": [],
					"homepage_order": {}
				}
				new_user = User(**user_kwargs)
				db.session.add(new_user)
			db.session.commit()
		return redirect(url_for("admin"))

	return render_template(
		"admin.html",
		invite_form=invite_form,
		hosted_sounds=app.available_sounds,
		css="admin.css",
		js=["admin.js"]
	)


@login_required
@app.route("/test", methods=["GET"])
def test():
	# new_invite = Invite(
	# 	id="test2",
	# 	valid=True,
	# 	role="admin",
	# 	place_holder={"firstname": "Tom", "lastname": "Jones"},
	# 	active_features=["test"],
	# 	homepage_order={"test1": 0, "test2": 1}
	# )
	# db.session.add(new_invite)
	# db.session.commit()

	# print(Invite.query.filter_by(id="test").first().active_features)
	# user = User.query.filter_by(id=current_user.id).first()
	# user.active_features = ['manage_blog', 'test', 'admin']
	# db.session.commit()
	#
	# cast = {
	# 	"named": {
	# 		"Martin Powell": ["hoqd7hpLMEhKLmUp"],
	# 		"Detective Inspector Bruton": ["Bh87kEAHtE2E6BpL"],
	# 		"Celia Wallis": ["MFr9Z1NbbV216bGa"],
	# 		"Detective Sergeant Fisher": ["cu6br_Ml4GPs72No"],
	# 		"WPC Leach": ["F-nKx-r96R2Ds2nR"],
	# 		"Detective Constable Wilkins": ["sEA0mysoRAgiBJ3E"],
	# 		"Neville Smallwood": ["mpxllfyccwYt3v-a"]
	# 	},
	# 	"grouped": {
	#
	# 	}
	# }
	#
	# crew = {
	# 	"Lighting": ["-xbPkjZ4cYTPeWpa"],
	# 	"Sound": ["QSaOM3ZMlRpGXR3E"],
	# 	"Stage Manager": ["sEA0mysoRAgiBJ3E"],
	# 	"Prompt": ["2kfIhKOywfSZ2mgV"],
	# 	"Wardrobe": ["PBgTI36I_LvDxdyr"],
	# 	"Props": ["HxD5_T14h9bu1d6k"],
	# 	"Set Design": ["PBgTI36I_LvDxdyr"],
	# 	"Set Construction": ["-xbPkjZ4cYTPeWpa", "NvOFvgrGOmdpj9ck"],
	# 	"Make-up": ["2kfIhKOywfSZ2mgV"],
	# 	"Front of House": ["hYb3oyjFNimuFs4j"],
	# 	"Ticket Sales": ["pWWJs9XBodLfz3BG"],
	# 	"Poster/Programme Design": ["ftou71eM0KIYAyZ6"],
	# 	"Publicity": ["mpxllfyccwYt3v-a", "HxD5_T14h9bu1d6k"]
	# }
	#
	# new_show = Show(
	# 	id="test_show",
	# 	year=2015,
	# 	season="Autumn",
	# 	show_type="Show",
	# 	title="Silhouette",
	# 	subtitle="a Thriller By Simon Brett",
	# 	cast_dict=cast,
	# 	crew_dict=crew
	# )
	#
	# db.session.add(new_show)
	# db.session.commit()



	return render_template("test.html", css="test.css", js=["test.js"])


@app.route("/login", methods=["GET", "POST"])
def login():
	if current_user.is_authenticated:
		return redirect(url_for("test"))

	login_form = LoginForm()
	register_form = Register()
	signup_key = request.args.get("key")
	if signup_key is None:
		signup_key = ""

	if request.method == "POST":
		form_type = ""
		try:
			# get string to identify if the login form or the register form was submitted
			form_type = request.form["spl_form_type"]
		except KeyError:
			try:
				form_type = request.form["spr_form_type"]
			except KeyError:
				abort(404)

		# login form logic
		if form_type == "login":
			user = User.query.filter_by(email=login_form.spl_email.data).first()
			if user is None:
				user = User.query.filter_by(username=login_form.spl_email.data).first()
			if user is not None and user.verify_password(login_form.spl_password.data):
				login_user(user)
				return redirect(url_for('test'))
			else:
				return redirect(url_for("login"))

		# register form logic
		elif form_type == "register":
			invite = Invite.query.filter_by(id=register_form.spr_signup_key.data).first_or_404()
			if invite.valid:
				kwargs = {
					"username": str(register_form.spr_username.data),
					"firstname": str(register_form.spr_firstname.data),
					"lastname": str(register_form.spr_lastname.data),
					"email": str(register_form.spr_email.data),
					"password": str(register_form.spr_password.data),
					"role": invite.role,
					"active_features": invite.active_features,
					"homepage_order": invite.homepage_order
				}
				user = "variable placeholder"
				if not invite.place_holder:
					used_ids = [value[0] for value in User.query.with_entities(User.id).all()]
					new_id = corha.rand_string(register_form.spr_email.data, 16, used_ids)
					kwargs["id"] = new_id
					new_user = User(**kwargs)
					db.session.add(new_user)
				else:
					user = User.query.filter_by(id=Invite.place_holder).first_or_404()
					user.update(**kwargs)

				invite.valid = False
				db.session.commit()
				login_user(user)
				return redirect(url_for("test"))
			else:
				return redirect(url_for("login"))
	else:
		return render_template(
			"login.html",
			login=login_form,
			register=register_form,
			signup_key=signup_key,
			css="login.css",
			js=["login.js"]
		)


@app.route("/logout")
def logout():
	logout_user()
	return redirect(url_for('login'))


# static files loader route, capable of loading multiple files of either js or css but not together
@app.route("/static", methods=["GET"])
def static_loader():
	"""
	GET:
		description: single route for requesting concatenated static files, either JS or CSS

		args:
			t: type of file, either "js" or "css"
			q: filenames of requested files in order, separated by "&" in the url

		security: None required
		responses:
			200: returns the requested js or css files all concatenated together

			404: error not found if the requested filetype is neither js or css
	:authors:
		- Matt
	:returns: HTTP Response
	"""
	# lookup table for mimetypes
	mimetype_lookup = {
		"js": "text/javascript",
		"css": "text/css"
	}
	# load url args from request object
	args = request.args
	filetype = args["t"]
	if filetype == "js":
		try:
			# check the static content cache for the requested combination
			output_blob = app.static_content_cache[filetype][args["q"]]
		except KeyError:
			file_list = args["q"].split(" ")
			output = []
			for file in file_list:
				if file != '':
					# load and concatenate all of the requested files
					with open(
							str(app.root + "/webapp/static/" + filetype + "/" + file).replace("\\", "/"),
							"r") as contents:
						output.append(contents.read())
			# create http response from concatenated files
			output_blob = "\n".join(output)

		response = make_response(output_blob)
		# set correct mimetype for response
		response.mimetype = mimetype_lookup[filetype]
		return response
	elif filetype == "css":
		files = request.args.to_dict(flat=False)['q'][0].split(" ")
		output = []
		for file in files:
			# if file in app.available_css:
			# 	if (content := app.static_content_cache[filetype].get(file)) is not None:
			# 		output.append(content)
			# 	else:
			# 		with open(str(app.root + "/webapp/static/css/" + file), "r") as contents:
			# 			output.append(contents.read())
			# 			app.static_content_cache[filetype][file] = output[-1]
			if (new_file := file[:-4] + ".scss") in app.available_scss:
				if app.config["FLASK_ENV"] == "development":
					with open(str(app.root + "/webapp/static/scss/" + new_file), "r") as contents:
						output.append(app.scss_compiler.compile_string(contents.read()))
				else:
					output.append(app.static_content_cache[filetype].get(file))
			else:
				abort(404)

		output_blob = "\n".join(output)
		response = make_response(output_blob)
		# set correct mimetype for response
		response.mimetype = mimetype_lookup[filetype]
		return response
	elif filetype == "img":
		filename = args["q"]
		return send_file(app.root + "/webapp/static/" + filetype + "/" + filename, mimetype='image/jpg')
	else:
		abort(404)

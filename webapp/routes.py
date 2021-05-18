from webapp import app, db
from flask import request, make_response, abort, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, AnonymousUserMixin, login_required
from webapp.forms import LoginForm, Register
from webapp.models import User, Invite


@app.route("/test", methods=["GET"])
def test():

	# new_invite = Invite(
	# 	id="test",
	# 	valid=True,
	# 	role="admin",
	# 	active_features=["test"],
	# 	homepage_order={"test1": 0, "test2": 1}
	# )
	# db.session.add(new_invite)
	# db.session.commit()

	# print(Invite.query.filter_by(id="test").first().active_features)
	css = []
	return render_template("test.html", css=css)


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
		try:
			# get string to identify if the login form or the register form was submitted
			form_type = request.form["spl_form_type"]
		except KeyError:
			try:
				form_type = request.form["spr_form_type"]
			except KeyError:
				abort(404)
		if form_type == "login":
			user = User.query.filter_by(email=login_form.spl_email.data).first()
			if user is None:
				user = User.query.filter_by(username=login_form.spl_email.data).first()
			if user is not None and user.verify_password(login_form.spl_password.data):
				return redirect(url_for('test'))
			else:
				print("TEST")
				flash("test")
		elif form_type == "register":
			id = str(register_form.spr_signup_key.data)
			invite = Invite.query.filter_by(id=id).first_or_404()
			if invite.valid:
				new_user = User(
					id=id,
					username=str(register_form.spr_username.data),
					firstname=str(register_form.spr_firstname.data),
					lastname=str(register_form.spr_lastname.data),
					email=str(register_form.spr_email.data),
					password=str(register_form.spr_password.data),
					role=invite.role,
					active_features=invite.active_features,
					homepage_order=invite.homepage_order
				)
				db.session.add(new_user)
				invite.valid = False
				db.session.commit()
				return redirect(url_for("test"))
			else:
				return redirect(url_for("login"))
	else:
		css = ["login.css"]
		return render_template("login.html", login=login_form, register=register_form, css=css)


# static files loader route, capable of loading multiple files of either js or css but not together
# TODO add caching for previously requested file lists
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
	if filetype in ["js", "css"]:
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
		response = make_response("\n".join(output))
		# set correct mimetype for response
		response.mimetype = mimetype_lookup[filetype]
		return response
	else:
		abort(404)

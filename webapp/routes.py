import corha.corha as corha
import dotmap
from webapp import app, db, socketio
from flask import request, make_response, abort, render_template, redirect, url_for, session, send_file
from flask_login import login_user, logout_user, current_user, login_required
from webapp.forms import LoginForm, Register, InviteForm
from webapp.models import User, Invite, BlogPost, BlogImage
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


@app.get("/blog")
def blog():
	if request.args:
		if "latest" in request.args.keys():
			post = BlogPost.query.order_by(BlogPost.date.desc()).first()
		else:
			post = BlogPost.query.filter_by(id=request.args.get("post")).first_or_404()
		author = User.query.filter_by(id=post.author).first()
		return render_template(
			"post.html",
			post=post,
			author=author,
			css=["back.css", "post.css"],
			js=[]
		)
	else:
		posts = BlogPost.query.order_by(BlogPost.date.desc()).all()
		return render_template(
			"blogs.html",
			posts=posts,
			css=["blogs.css"],
			js=[]
		)


@app.get("/manage_blog")
@login_required
def manage_blog():
	if current_user.is_authenticated:
		posts = []
		if current_user.role == "author":
			posts = BlogPost.query.filter_by(author=current_user.id).order_by(BlogPost.date.desc()).all()
		elif current_user.role == "admin":
			posts = BlogPost.query.order_by(BlogPost.date.desc()).all()
		return render_template(
			"manage_blogs.html",
			posts=posts,
			css=["popup.css", "blog_manager.css"],
			js=["popup.js", "blog_manager.js"]
		)
	else:
		return redirect(url_for("login"))


@app.post("/manage_blog/upload")
@login_required
def upload_blog():
	print(request.files.get('file').filename.rstrip(".docx"))
	used_ids = [value[0] for value in BlogPost.query.with_entities(BlogPost.id).all()]
	blog_id = corha.rand_string(datetime.utcnow().isoformat(), 16, used_ids)

	def convert_image(image, id=blog_id):
		img_count = BlogImage.query.filter_by(blog_id=id).count()
		with image.open() as image_bytes:
			pil_image = Image.open(image_bytes, "r", None)
			pil_image = pil_image.convert('RGB')
			b = io.BytesIO()
			pil_image.save(b, "JPEG")
			b.seek(0)

			new_img = BlogImage(
				blog_id=id,
				image_no=img_count,
				image=b.read()
			)
			db.session.add(new_img)
			db.session.commit()

		return {
			"title": f"image_{img_count}.jpg",
			"src": f"/blog_img/{id}/{img_count}"
		}

	result = mammoth.convert_to_markdown(
		request.files.get('file'),
		convert_image=mammoth.images.img_element(convert_image))

	# modify markdown to match github style

	# use ** to denote bold text rather than __
	markdown = result.value.replace("__", "**")
	# remove unnecessary character escaping
	markdown = markdown.replace("\\.", ".")\
		.replace("\\(", "(")\
		.replace("\\)", ")")\
		.replace("\\!", "!")
	# force https links
	markdown = markdown.replace("](http://", "](https://")
	# remove initial hr element
	markdown = markdown.replace("*** ***", "")

	for i in range(len(markdown)):
		if markdown[i] not in [" ", "\n"]:
			markdown = markdown[i:]
			break

	post = BlogPost(**{
		"id": blog_id,
		"date": datetime.utcnow(),
		"title": request.files.get('file').filename.rstrip(".docx"),
		"content": markdown,
		"category": "blogpost",
		"author": current_user.id,
		"views": 0
	})
	db.session.add(post)
	db.session.commit()
	return make_response(blog_id, 200)


@app.get("/manage_blog/editor")
@login_required
def blog_editor():
	if current_user.is_authenticated:
		js = ["popup.js", "marked.js"]
		is_new = False
		if "new" in request.args.keys():
			is_new = True
			used_ids = [value[0] for value in BlogPost.query.with_entities(BlogPost.id).all()]
			post = dotmap.DotMap({
				"id": corha.rand_string(datetime.utcnow().isoformat(), 16, used_ids),
				"date": datetime.utcnow(),
				"title": "",
				"content": ""
			})
			js = [*js, "newblog_editor.js"]
		else:
			post = BlogPost.query.filter_by(id=request.args.get("post")).first_or_404()
			js = [*js, "socket.io.min.js", "blog_editor.js"]
		return render_template(
			"blog_editor.html",
			post=post,
			isNew=is_new,
			user=current_user,
			css=["popup.css", "blog_editor.css", "back.css"],
			js=js
		)
	else:
		return redirect(url_for("login"))


@app.post("/blog_save")
def blog_save():
	used_ids = [value[0] for value in BlogPost.query.with_entities(BlogPost.id).all()]
	kwargs = {
		"id": corha.rand_string(datetime.utcnow().isoformat(), 16, used_ids),
		"title":  request.json["title"],
		"content": request.json["content"],
		"category": "blogpost",
		"author": request.json["author"],
		"date": datetime.utcnow()
	}
	new_post = BlogPost(**kwargs)
	db.session.add(new_post)
	db.session.commit()
	response = kwargs["id"]
	return response


@app.get("/blog_img/<blog_id>/<int:image_no>")
def blog_img(blog_id, image_no):
	img = BlogImage.query.get((blog_id, image_no)).image
	return make_response(img)


@socketio.on('edit', namespace="/manage_blog/edit")
def update_blog(data):
	post = BlogPost.query.filter_by(id=data["id"]).first_or_404()
	post.title = data["title"]
	post.content = data["content"]
	db.session.commit()
	emit('updated', data, broadcast=True, to=data["id"])


@socketio.on('join', namespace="/manage_blog/edit")
def handle_join(data):
	room = data["room"]
	user_id = data["user_id"]
	join_room(room)
	print(f'{user_id} joined room "{room}"')


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
				"active_features": [],
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
		css=[],
		js=[]
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

	return render_template("test.html", css=[], js=[])


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
			css=["login.css"],
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
	if filetype in ["js", "css"]:
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
	elif filetype == "img":
		filename = args["q"]
		return send_file(app.root + "/webapp/static/" + filetype + "/" + filename, mimetype='image/jpg')
	else:
		abort(404)

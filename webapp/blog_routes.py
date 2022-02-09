# generic imports
import io
from datetime import datetime
import dotmap
import mammoth
from PIL import Image
from corha import corha

# flask-specific imports
from flask import request, render_template, redirect, url_for, make_response, abort
from flask_login import login_required, current_user
from flask_socketio import emit, join_room

# local imports
from webapp import app, db, socketio
from webapp.models import BlogPost, User, BlogImage


@app.get("/blog")
def blog():
	if request.args:
		if "latest" in request.args.keys():
			post = BlogPost.query.order_by(BlogPost.date.desc()).first()
		else:
			post = BlogPost.query.filter_by(id=request.args.get("post")).first_or_404()
		author = User.query.filter_by(id=post.author).first()
		post.views += 1
		db.session.commit()
		return render_template(
			"post.html",
			post=post,
			author=author,
			css="post.css",
			js=[]
		)
	else:
		posts = BlogPost.query.order_by(BlogPost.date.desc()).all()
		return render_template(
			"blogs.html",
			posts=posts,
			css="blogs.css",
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
			css="blog_manager.css",
			js=["popup.js", "blog_manager.js"]
		)
	else:
		return redirect(url_for("login"))


@app.post("/manage_blog/upload")
@login_required
def upload_blog():
	used_ids = [value[0] for value in BlogPost.query.with_entities(BlogPost.id).all()]
	blog_id = corha.rand_string(datetime.utcnow().isoformat(), 16, used_ids)

	def convert_image(image, id=blog_id):
		img_count = BlogImage.query.filter_by(blog_id=id).count()
		sp_logo = BlogImage.query.get(("sitewide", 0)).image
		b = io.BytesIO()
		with image.open() as image_bytes:
			pil_image = Image.open(image_bytes, "r", None)
			pil_image = pil_image.convert('RGB')
			pil_image.save(b, "JPEG")
			b.seek(0)

		if b.read() == sp_logo:
			id = "sitewide"
			img_count = 0
		else:
			b.seek(0)
			new_img = BlogImage(
				blog_id=id,
				image_no=img_count,
				image=b.read()
			)
			db.session.add(new_img)
			db.session.commit()

		return {
			"src": f"/blog_img/{id}/{img_count}"
		}

	result = mammoth.convert_to_markdown(
		request.files.get('file'),
		convert_image=mammoth.images.img_element(convert_image))

	# modify markdown to match github style

	# use ** to denote bold text rather than __
	markdown = result.value.replace("__", "**")
	# remove unnecessary character escaping
	markdown = markdown.replace("\\.", ".") \
		.replace("\\(", "(") \
		.replace("\\)", ")") \
		.replace("\\!", "!") \
		.replace("\\-", "-") \
		.replace("\\_", "_")
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
		js = ["popup.js"]
		external_js = ["https://cdnjs.cloudflare.com/ajax/libs/marked/2.0.3/marked.min.js"]
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
			js = [*js, "blog_editor.js"]
			external_js = [
				*external_js,
				"https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.min.js"
			]
		return render_template(
			"blog_editor.html",
			post=post,
			isNew=is_new,
			user=current_user,
			css="blog_editor.css",
			js=js,
			external_js=external_js
		)
	else:
		return redirect(url_for("login"))


@app.post("/blog_save")
def blog_save():
	used_ids = [value[0] for value in BlogPost.query.with_entities(BlogPost.id).all()]
	kwargs = {
		"id": corha.rand_string(datetime.utcnow().isoformat(), 16, used_ids),
		"title": request.json["title"],
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
	if img is not None:
		return make_response(img)
	else:
		abort(404)


@socketio.on('edit', namespace="/manage_blog/edit")
def update_blog(data):
	post = BlogPost.query.filter_by(id=data["id"]).first_or_404()
	post.title = data["title"]
	post.content = data["content"]
	post.date = datetime.fromisoformat(data["date"])
	db.session.commit()
	emit('updated', data, broadcast=True, to=data["id"])


@socketio.on('join', namespace="/manage_blog/edit")
def handle_join(data):
	room = data["room"]
	user_id = data["user_id"]
	join_room(room)
	print(f'{user_id} joined room "{room}"')

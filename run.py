from jinja2 import environment

from webapp import app, routes, blog_routes, socketio  # , shows_routes
import socket

if __name__ == "__main__":
	hostname = socket.gethostname()
	if hostname == "BAIN":
		socketio.run(app, host='0.0.0.0')
	else:
		socketio.run(app, debug=True)

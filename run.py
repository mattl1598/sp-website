from webapp import app, routes, socketio
import socket

if __name__ == "__main__":
	hostname = socket.gethostname()
	if hostname == "BAIN":
		socketio.run(app, host='0.0.0.0')
	else:
		socketio.run(app, debug=True)

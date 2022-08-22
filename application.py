from web import socketio, app

socketio.run(app, use_reloader=False)
from web import socketio, app, core_data

if core_data.status == "online":
    socketio.run(app, use_reloader=False)
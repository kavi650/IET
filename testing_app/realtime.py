"""testing_app/realtime.py — Flask-SocketIO events for live test data."""


def register_events(socketio):

    @socketio.on('join_session')
    def on_join(data):
        from flask_socketio import join_room
        session_id = data.get('session_id')
        if session_id:
            join_room(f'session_{session_id}')

    @socketio.on('leave_session')
    def on_leave(data):
        from flask_socketio import leave_room
        session_id = data.get('session_id')
        if session_id:
            leave_room(f'session_{session_id}')

    @socketio.on('connect')
    def on_connect():
        socketio.emit('connected', {'status': 'ok'})

    @socketio.on('disconnect')
    def on_disconnect():
        pass

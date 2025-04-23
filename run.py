#!/usr/bin/env python
import os
from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, debug=app.config['DEBUG'], host='0.0.0.0', port=port)
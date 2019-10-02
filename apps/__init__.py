import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
socketio = SocketIO(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'

from apps.logger import bp as logger_bp
app.register_blueprint(logger_bp, url_prefix='/logger')

from apps.pos import bp as lokasi_bp
app.register_blueprint(lokasi_bp, url_prefix='/pos')

from apps.tma import bp as tma_bp
app.register_blueprint(tma_bp, url_prefix='/tma')

from apps.curahhujan import bp as curahhujan_bp
app.register_blueprint(curahhujan_bp, url_prefix='/curahhujan')

from apps.raw import bp as raw_bp
app.register_blueprint(raw_bp, url_prefix='/raw')

from apps import routes, models, command

if __name__ == '__main__':
    socketio.run(app)

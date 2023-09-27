from __future__ import annotations

from flask import send_from_directory, Response
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_compress import Compress

from endpoints.authorization import authorization
from endpoints.api import api

from utils import User, AddStaticFileHashFlask, get_user, send_error, update_database
from var import *


app = AddStaticFileHashFlask(__name__)
DEBUG = os.getenv("debug")

SECRET_KEY = os.getenv("SECRET_KEY") if os.getenv("SECRET_KEY") else "DEBUG_KEY"
app.secret_key = SECRET_KEY
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = 32140800

compress = Compress()
compress.init_app(app)

csrf = CSRFProtect(app)
csrf.init_app(app)


# authorization
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# endpoints
app.register_blueprint(authorization)
app.register_blueprint(api)


@login_manager.user_loader
def user_loader(user_id: str) -> User | None:
    tmp_user = get_user(user_id)
    if tmp_user is None:
        return
    tmp_user = User(user_id)
    return tmp_user


@login_manager.unauthorized_handler
def unauthorized_callback() -> Response:
    return send_error("Für diese Anfrage musst du eingeloggt sein.")


# COMPILED SVELTE FILES
@app.route("/", methods=["GET"])
def base() -> Response:
    resp = send_from_directory('client/public', 'index.html')
    resp.set_cookie("csrftoken", generate_csrf())
    return resp


@app.route("/public/<path:path>", methods=["GET"])
def home(path) -> Response:
    return send_from_directory('client/public', path)


@app.route("/serviceworker.js", methods=["GET"])
def sw() -> Response:
    return send_from_directory('client/public', 'serviceworker.js')


if __name__ == "__main__":
    update_database()
    app.run(debug=DEBUG)

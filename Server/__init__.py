from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_jwt_extended import JWTManager

# from sqlalchemy import inspect
from secrets import token_hex
from datetime import timedelta
from dotenv import load_dotenv
from os import getenv, path
from os.path import join, dirname
# from gevent.pywsgi import WSGIServer

from .static.predef_function.server_credentials import EMAIL, PASSWORD


server: Flask = Flask(__name__)
db: SQLAlchemy = SQLAlchemy()
mail: Mail = Mail()
jwt: JWTManager = JWTManager()
dotenv_path = join(dirname(__file__), "static", ".env")
load_dotenv(dotenv_path)


CORS(
    server,
    resources={
        r"/*": {"origins": getenv("CORS_ADDRESS")}
    }
)


class Flaskserver:
    DB_NAME = "database.db"

    def __init__(self):

        self.server = server
        # self.http_server = WSGIServer(("127.0.0.1", 5000), self.server)

        self.server.config["SECRET_KEY"] = token_hex(128)
        self.server.config["JWT_SECRET_KEY"] = token_hex(128)
        self.server.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
        self.server.config["SECURITY_PASSWORD_SALT"] = token_hex(128)
        # self.server.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URI")
        self.server.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{self.DB_NAME}"
        self.server.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.server.config["MAIL_SERVER"] = getenv("MAIL_SERVER")
        self.server.config["MAIL_PORT"] = 587
        self.server.config["MAIL_USE_TLS"] = True
        self.server.config["MAIL_USE_SSL"] = False
        self.server.config["MAIL_USERNAME"] = EMAIL
        self.server.config["MAIL_PASSWORD"] = PASSWORD
        self.server.config["MAIL_DEFAULT_SENDER"] = EMAIL

        db.init_app(self.server)
        mail.init_app(self.server)
        jwt.init_app(self.server)

        from .models import User, Captcha, Revoked, Resend, Reset, Template, Credentials, Documents
        from .authentication import auth
        from .views import views

        self.server.register_blueprint(auth, url_prefix="/")
        self.server.register_blueprint(views, url_prefix="/")

        # try:
        #     tables: list[str] = [
        #         "user",
        #         "captcha",
        #         "revoked",
        #         "resend",
        #         "reset",
        #         "template",
        #         "documents",
        #         "credentials",

        #     ]

        #     with self.server.app_context():
        #         with db.engine.connect() as connection:
        #             inspector = inspect(connection)

        #             for table in tables:
        #                 if table not in inspector.get_table_names():
        #                     db.create_all()

        # except Exception:
        #     print("Please enable you database connection!")

        with self.server.app_context():
            if not path.exists(self.DB_NAME):
                db.create_all()

        @jwt.user_identity_loader
        def user_loader(user) -> int:
            return user.id

        @jwt.user_lookup_loader
        def user_lookup_callback(_jwt_header, decoded_token):
            identity = decoded_token["sub"]
            return User.query.get(int(identity))

        @jwt.token_in_blocklist_loader
        def revoked_tokens(jwt_header, decoded_token) -> bool:
            jti = decoded_token['jti']
            revoked_token: Revoked = Revoked.query.filter_by(jti=jti).scalar()
            return revoked_token is not None

    def server_run(self):
        # return self.http_server
        return self.server

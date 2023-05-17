from flask import Flask, jsonify
from flask_smorest import Api 
from flask_jwt_extended import JWTManager
import secrets
import os
from db import db
import models

from resources.item import blp as ItemsBlueprint
from resources.store import blp as StoreBlueprint
from resources.tag import blp as TagBlueprint
from resources.user import blp as UserBlueprint

def create_app(db_url=None):
    app = Flask(__name__)

    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "Stores REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "http://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv("DATABASE_URL", "sqlite:///data.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    api = Api(app)

    #app.config["JWT_SECRET_KEY"] = secrets.SystemRandom().getrandbits(128)

    app.config["JWT_SECRET_KEY"] = "283594143424053833908381604084545970094"

    jwt = JWTManager(app)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return (
            jsonify (
                {"message":"The token has expired.", "error":"token_expired"}
            ),
            401,
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            jsonify (
                {"message":"Signature verification failed.", "error":"invalid_token"}
            ),
            401,
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            jsonify (
                {"description":"Request does not contain an access token.",
                 "error":"authorization_required"}
            ),
            401,
        )

    @app.before_first_request
    def create_tables():
        db.create_all()

    api.register_blueprint (ItemsBlueprint)
    api.register_blueprint (StoreBlueprint)
    api.register_blueprint (TagBlueprint)
    api.register_blueprint (UserBlueprint)

    return app
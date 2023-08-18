import requests
import os
from flask import current_app

from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import or_
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    get_jwt,
    jwt_required,
)

from db import db
from blocklist import BLOCKLIST

from models import UserModel
from schemas import UserSchema

from tasks import send_user_registration_email

blp = Blueprint("Users", "users", description="Operations on users")

@blp.route("/user/<string:user_id>")
class User(MethodView):
    @blp.response(200, UserSchema)
    @jwt_required()
    def get(cls, user_id):
        user = UserModel.query.get_or_404(user_id)
        return user

    def delete(cls, user_id):
        user = UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {"message":"User deleted"}

@blp.route("/register")
class UserList(MethodView):
    @blp.arguments(UserSchema)
    @blp.response(201, UserSchema)
    def post(cls, user_data):
        if UserModel.query.filter(
            or_(
                UserModel.username == user_data["username"],
                UserModel.email == user_data["email"]
            )
        ).first():
            abort(409, message="Username already exists")

        password = pbkdf2_sha256.hash(user_data["password"])
        new_user = UserModel(username=user_data["username"], email=user_data["email"], password=password)

        try:
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError:
            abort(400, message="User name already in use")
        except SQLAlchemyError as e:
            abort(500, message=str(e))

        current_app.queue.enqueue(send_user_registration_email, new_user.email, new_user.username)

        return {"message" : "User created successfully."}, 201

@blp.route("/login")
class UserLogin(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel.query.filter(UserModel.username == user_data["username"]
        ).first()

        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            access_token = create_access_token(identity=user.id, fresh=True)
            refresh_token = create_refresh_token(user.id)
            return {"access_token": access_token, "refresh_token":refresh_token}, 200
        
        abort(401, message="Invalid credentials")

@blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"message": "Succeffully logged out"}

@blp.route("/refresh")
class TokenRefresh(MethodView):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"access_token":new_token}, 200
import uuid
from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from models import StoreModel
from db import db
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from schemas import StoreSchema

blp = Blueprint("Stores", "store", description="Operations on stores")

@blp.route("/store/<int:store_id>")
class Store(MethodView):
    @blp.response(200, StoreSchema)
    def get(cls, store_id):
        store = StoreModel.query.get_or_404(store_id)
        return store

    def delete(cls, store_id):
        store = StoreModel.query.get_or_404(store_id)
        db.session.delete(store)
        db.session.commit()
        return {"message":"Store deleted"}

@blp.route("/store")
class StoreList(MethodView):
    @blp.response(200, StoreSchema(many=True))
    def get(cls):
        return StoreModel.query.all()
    
    @blp.arguments(StoreSchema)
    @blp.response(201, StoreSchema)
    def post(cls, store_data):
        new_store = StoreModel(**store_data)
        try:
            db.session.add(new_store)
            db.session.commit()
        except IntegrityError:
            abort(400, "Store name already in use")
        except SQLAlchemyError:
            abort(500, "An error occurred while creating Store")

        return new_store
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from db import db

from models import TagModel, StoreModel, ItemModel
from schemas import TagSchema, TagAndItemSchema

blp = Blueprint("Tags", "tags", description="Operations on tags")

@blp.route("/store/<string:store_id>/tag")
class TagsInStore(MethodView):

    @blp.response(200, TagSchema(many=True))
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)

        return store.tags.all()
    
    @blp.arguments(TagSchema)
    @blp.response(201, TagSchema)
    def post(self, tag_data, store_id):
        if TagModel.query.filter(TagModel.store_id == store_id, TagModel.name == tag_data["name"]).first():
            abort (400, message="A tag with the same name already exists in that store")

        tag = TagModel(**tag_data, store_id=store_id)
        try:
            db.session.add(tag)
            db.session.commit()
        except IntegrityError as e:
            abort(400, message=str(e))
        except SQLAlchemyError as e:
            abort(500, message=str(e))
        
        return tag

@blp.route("/item/<string:item_id>/tag/<string:tag_id>")
class LinkTagsToItem(MethodView):
    @blp.response(201, TagSchema)
    def post(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag  = TagModel.query.get_or_404(tag_id)

        if item.store_id != tag.store_id:
            abort(500, message="Store id does not match:")

        item.tags.append(tag)

        try:
            db.session.add(item)
            db.session.commit()
        
        except SQLAlchemyError as e:
            abort(500, message="Error while inserting tag:" + str(e))

        return tag
    
    @blp.response(200, TagAndItemSchema)
    def delete(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag  = ItemModel.query.get_or_404(tag_id)

        if item.store_id != tag.store_id:
            abort(500, message="Store id does not match:")
        
        item.tags.remove(tag)

        try:
            db.session.add(item)
            db.session.commit()
        
        except SQLAlchemyError as e:
            abort(500, message="Error while removing tag:" + str(e))
        
        return {"message": "Item removed: ", "item":item, "tag": tag}



@blp.route("/tag/<string:tag_id>")
class Tag(MethodView):
    @blp.response(200, TagSchema)
    def get(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        return tag

    @blp.response(202, description="Deletes a tag if no item is tagged with it",
    example = {"message": "Tag deleted"}
    )
    @blp.alt_response(404, description="Tag not found")
    @blp.alt_response(400, description="Tag assigned to one or more items.")
    def delete(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)

        if not tag.items:
            db.session.delete(tag)
            db.session.commit()
            return {"message":"Tag Deleted"}
        
        abort(
            400,
            message="Could not delete tag. Make sure tag is not linked to any item"
            )

@blp.route("/tag")
class Tag(MethodView):
    @blp.response(200, TagSchema(many=True))
    def get(self):
        try:
            tag = TagModel.query.all()
        except SQLAlchemyError as e:
            abort(404, message=str(e))
        
        return tag
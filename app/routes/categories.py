from flask import abort
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.category import Category
from app.schemas.category import CategorySchema

blp = Blueprint("categories", __name__, url_prefix="/api/categories", description="Category management")


@blp.route("/", methods=["GET"])
@blp.response(200, CategorySchema(many=True))
def list_categories():
    """List all categories."""
    return Category.query.order_by(Category.name).all()


@blp.route("/", methods=["POST"])
@blp.arguments(CategorySchema)
@blp.response(201, CategorySchema)
@blp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def create_category(data):
    """Create a new category (requires JWT)."""
    if Category.query.filter_by(name=data["name"]).first():
        abort(409, description="Category name already exists.")

    category = Category(name=data["name"])
    db.session.add(category)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(409, description="Category name already exists.")
    return category


@blp.route("/<int:category_id>", methods=["PUT"])
@blp.arguments(CategorySchema)
@blp.response(200, CategorySchema)
@blp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def update_category(data, category_id):
    """Update a category (requires JWT)."""
    category = db.get_or_404(Category, category_id)

    existing = Category.query.filter_by(name=data["name"]).first()
    if existing and existing.id != category_id:
        abort(409, description="Category name already exists.")

    category.name = data["name"]
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(409, description="Category name already exists.")
    return category


@blp.route("/<int:category_id>", methods=["DELETE"])
@blp.response(204)
@blp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def delete_category(category_id):
    """Delete a category (requires JWT). Returns 409 if posts still exist in this category."""
    category = db.get_or_404(Category, category_id)

    if category.posts.count() > 0:
        abort(409, description="Cannot delete category: posts are still assigned to it.")

    db.session.delete(category)
    db.session.commit()

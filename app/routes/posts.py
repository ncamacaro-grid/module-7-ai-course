from flask import abort, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_smorest import Blueprint

from app.extensions import db
from app.models.post import Post
from app.models.category import Category
from app.schemas.post import PostSchema, PostInputSchema, PostUpdateSchema

blp = Blueprint("posts", __name__, url_prefix="/api/posts", description="Blog post CRUD")


@blp.route("/", methods=["GET"])
@blp.response(200, PostSchema(many=True))
def list_posts():
    """List all posts with pagination."""
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
    except ValueError:
        abort(400, description="page and per_page must be integers.")

    if page < 1 or per_page < 1:
        abort(400, description="page and per_page must be positive integers.")

    paginated = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return paginated.items


@blp.route("/", methods=["POST"])
@blp.arguments(PostInputSchema)
@blp.response(201, PostSchema)
@blp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def create_post(data):
    """Create a new post (requires JWT)."""
    author_id = int(get_jwt_identity())

    if data.get("category_id") is not None:
        if not db.session.get(Category, data["category_id"]):
            abort(400, description="Category not found.")

    post = Post(
        title=data["title"],
        content=data["content"],
        author_id=author_id,
        category_id=data.get("category_id"),
    )
    db.session.add(post)
    db.session.commit()
    return post


@blp.route("/<int:post_id>", methods=["GET"])
@blp.response(200, PostSchema)
def get_post(post_id):
    """Retrieve a single post."""
    return db.get_or_404(Post, post_id)


@blp.route("/<int:post_id>", methods=["PUT"])
@blp.arguments(PostUpdateSchema)
@blp.response(200, PostSchema)
@blp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def update_post(data, post_id):
    """Update a post (requires JWT, owner only)."""
    post = db.get_or_404(Post, post_id)
    current_user_id = int(get_jwt_identity())

    if post.author_id != current_user_id:
        abort(403, description="You are not the owner of this post.")

    if "category_id" in data and data["category_id"] is not None:
        if not db.session.get(Category, data["category_id"]):
            abort(404, description="Category not found.")

    if "title" in data:
        post.title = data["title"]
    if "content" in data:
        post.content = data["content"]
    if "category_id" in data:
        post.category_id = data["category_id"]

    db.session.commit()
    return post


@blp.route("/<int:post_id>", methods=["DELETE"])
@blp.response(204)
@blp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def delete_post(post_id):
    """Delete a post (requires JWT, owner only)."""
    post = db.get_or_404(Post, post_id)
    current_user_id = int(get_jwt_identity())

    if post.author_id != current_user_id:
        abort(403, description="You are not the owner of this post.")

    db.session.delete(post)
    db.session.commit()

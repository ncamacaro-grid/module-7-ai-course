from flask import abort, request
from flask_smorest import Blueprint

from app.models.post import Post
from app.schemas.post import PostSchema

blp = Blueprint("search", __name__, url_prefix="/api/search", description="Search")


@blp.route("/", methods=["GET"])
@blp.response(200, PostSchema(many=True))
def search_posts():
    """Search posts by title or content. Requires ?q=<keyword>."""
    q = request.args.get("q", "").strip()
    if not q:
        abort(400, description="Search query 'q' is required and cannot be blank.")

    pattern = f"%{q}%"
    results = Post.query.filter(
        Post.title.ilike(pattern) | Post.content.ilike(pattern)
    ).order_by(Post.created_at.desc()).all()

    return results

from flask import abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_smorest import Blueprint

from app.extensions import db
from app.models.post import Post
from app.models.comment import Comment
from app.schemas.comment import CommentSchema, CommentInputSchema

blp = Blueprint("comments", __name__, description="Comment system")


@blp.route("/api/posts/<int:post_id>/comments", methods=["GET"])
@blp.response(200, CommentSchema(many=True))
def list_comments(post_id):
    """List all comments for a post."""
    post = db.get_or_404(Post, post_id)
    return post.comments.order_by(Comment.created_at.asc()).all()


@blp.route("/api/posts/<int:post_id>/comments", methods=["POST"])
@blp.arguments(CommentInputSchema)
@blp.response(201, CommentSchema)
@blp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def create_comment(data, post_id):
    """Add a comment to a post (requires JWT)."""
    post = db.get_or_404(Post, post_id)
    author_id = int(get_jwt_identity())

    comment = Comment(
        content=data["content"],
        author_id=author_id,
        post_id=post.id,
    )
    db.session.add(comment)
    db.session.commit()
    return comment


@blp.route("/api/comments/<int:comment_id>", methods=["DELETE"])
@blp.response(204)
@blp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def delete_comment(comment_id):
    """Delete a comment (requires JWT). Allowed for the comment owner or the post owner."""
    comment = db.get_or_404(Comment, comment_id)
    current_user_id = int(get_jwt_identity())

    if comment.author_id != current_user_id and comment.post.author_id != current_user_id:
        abort(403, description="You are not allowed to delete this comment.")

    db.session.delete(comment)
    db.session.commit()

from flask import abort
from flask_jwt_extended import create_access_token
from flask_smorest import Blueprint
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.user import User
from app.schemas.auth import RegisterSchema, LoginSchema, UserSchema

blp = Blueprint("auth", __name__, url_prefix="/api/auth", description="Authentication")


@blp.route("/register", methods=["POST"])
@blp.arguments(RegisterSchema)
@blp.response(201, UserSchema)
def register(data):
    """Register a new user."""
    email = data["email"].lower()

    if User.query.filter_by(email=email).first():
        abort(409, description="Email already registered.")
    if User.query.filter_by(username=data["username"]).first():
        abort(409, description="Username already taken.")

    user = User(username=data["username"], email=email)
    user.set_password(data["password"])
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(409, description="A user with that email or username already exists.")
    return user


@blp.route("/login", methods=["POST"])
@blp.arguments(LoginSchema)
@blp.response(200)
def login(data):
    """Login and receive a JWT access token."""
    email = data["email"].lower()
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(data["password"]):
        abort(401, description="Invalid email or password.")

    token = create_access_token(identity=str(user.id))
    return {"access_token": token}

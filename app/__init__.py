import os
from flask import Flask
from flask_smorest import Api

from app.config import get_config
from app.extensions import db, jwt
from app.errors import register_error_handlers, register_jwt_handlers


def create_app(env: str = None) -> Flask:
    if env is None:
        env = os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__)
    app.config.from_object(get_config(env))

    if env == "production":
        missing = [k for k in ("SECRET_KEY", "JWT_SECRET_KEY") if not app.config.get(k)]
        if missing:
            raise RuntimeError(
                f"Production requires environment variables to be set: {', '.join(missing)}"
            )

    db.init_app(app)
    jwt.init_app(app)

    api = Api(app)

    from app.routes.auth import blp as auth_blp
    from app.routes.categories import blp as categories_blp
    from app.routes.posts import blp as posts_blp
    from app.routes.comments import blp as comments_blp
    from app.routes.search import blp as search_blp

    api.register_blueprint(auth_blp)
    api.register_blueprint(categories_blp)
    api.register_blueprint(posts_blp)
    api.register_blueprint(comments_blp)
    api.register_blueprint(search_blp)

    register_error_handlers(app)
    register_jwt_handlers(jwt)

    with app.app_context():
        db.create_all()

    return app

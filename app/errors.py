from flask import jsonify
from werkzeug.exceptions import HTTPException


def _error_response(error_type: str, message: str, status: int, details: dict = None):
    """Always include 'details'; defaults to {} when nothing to report."""
    body = {
        "error": error_type,
        "message": message,
        "details": details if details is not None else {},
    }
    return jsonify(body), status


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return _error_response("BadRequest", str(e.description), 400)

    @app.errorhandler(401)
    def unauthorized(e):
        return _error_response("Unauthorized", str(e.description), 401)

    @app.errorhandler(403)
    def forbidden(e):
        return _error_response("Forbidden", str(e.description), 403)

    @app.errorhandler(404)
    def not_found(e):
        return _error_response("NotFound", str(e.description), 404)

    @app.errorhandler(409)
    def conflict(e):
        return _error_response("Conflict", str(e.description), 409)

    # Flask-Smorest/webargs raises 422 for schema validation failures.
    # The exercise requires validation errors to return 400.
    @app.errorhandler(422)
    def unprocessable(e):
        details = getattr(e, "data", {}).get("messages", {})
        return _error_response("ValidationError", "Invalid request payload", 400, details)

    @app.errorhandler(HTTPException)
    def handle_http(e):
        return _error_response(e.name.replace(" ", ""), e.description, e.code)

    @app.errorhandler(Exception)
    def handle_generic(e):
        app.logger.exception("Unhandled exception")
        return _error_response("InternalServerError", "An unexpected error occurred.", 500)


def register_jwt_handlers(jwt):
    """Register Flask-JWT-Extended error callbacks to return the standard error shape."""

    @jwt.unauthorized_loader
    def missing_token(error_string):
        return _error_response("Unauthorized", "Authorization token is missing.", 401)

    @jwt.invalid_token_loader
    def invalid_token(error_string):
        return _error_response("Unauthorized", "Authorization token is invalid.", 401)

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return _error_response("Unauthorized", "Authorization token has expired.", 401)

    @jwt.revoked_token_loader
    def revoked_token(jwt_header, jwt_payload):
        return _error_response("Unauthorized", "Authorization token has been revoked.", 401)

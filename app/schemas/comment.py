from marshmallow import Schema, fields, validate


class CommentInputSchema(Schema):
    content = fields.Str(required=True, validate=validate.Length(min=1))


class CommentSchema(Schema):
    id = fields.Int(dump_only=True)
    content = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    author_id = fields.Int(dump_only=True)
    post_id = fields.Int(dump_only=True)

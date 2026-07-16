from marshmallow import Schema, fields, validate


class PostInputSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    content = fields.Str(required=True, validate=validate.Length(min=1))
    category_id = fields.Int(load_default=None)


class PostUpdateSchema(Schema):
    title = fields.Str(validate=validate.Length(min=1, max=200))
    content = fields.Str(validate=validate.Length(min=1))
    # No load_default: omitting category_id preserves the current value.
    # Sending null explicitly clears it. Sending an integer reassigns it.
    category_id = fields.Int(allow_none=True)


class PostSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(dump_only=True)
    content = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    author_id = fields.Int(dump_only=True)
    category_id = fields.Int(dump_only=True, allow_none=True)

"""
Tests verifying that the SQLAlchemy-declared database indexes are actually
created in the SQLite schema by db.create_all().

These tests inspect the live database schema, not just the model declarations,
so they catch any mismatch between ORM metadata and what SQLite stores.

Important note on existing databases
-------------------------------------
db.create_all() creates tables and indexes that do not yet exist, but it
does NOT modify tables or add indexes to an already-existing database
(i.e. instance/blog.db). Any database file created before these index
declarations were added must be recreated — or migrated with a tool such
as Alembic — to gain these indexes. The test suite uses an in-memory
SQLite database that is rebuilt fresh for every test run.
"""
import pytest
from sqlalchemy import inspect


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get_index_names(engine, table_name: str) -> set[str]:
    """Return the set of all index names on a given table."""
    inspector = inspect(engine)
    return {idx["name"] for idx in inspector.get_indexes(table_name)}


def _get_indexed_columns(engine, table_name: str) -> dict[str, set[str]]:
    """Return a mapping of index_name -> set of column names."""
    inspector = inspect(engine)
    return {
        idx["name"]: set(idx["column_names"])
        for idx in inspector.get_indexes(table_name)
    }


# ---------------------------------------------------------------------------
# posts table — required indexes
# (db fixture is required so that create_all() has been called)
# ---------------------------------------------------------------------------

def test_ix_posts_category_id_exists(app, db):
    """ix_posts_category_id must exist on the posts table."""
    with app.app_context():
        names = _get_index_names(db.engine, "posts")
        assert "ix_posts_category_id" in names, (
            f"Expected index 'ix_posts_category_id' on posts, found: {names}"
        )


def test_ix_posts_category_id_covers_correct_column(app, db):
    """ix_posts_category_id must cover the category_id column."""
    with app.app_context():
        indexed = _get_indexed_columns(db.engine, "posts")
        assert indexed.get("ix_posts_category_id") == {"category_id"}, (
            f"ix_posts_category_id covers wrong columns: {indexed.get('ix_posts_category_id')}"
        )


def test_ix_posts_created_at_exists(app, db):
    """ix_posts_created_at must exist on the posts table."""
    with app.app_context():
        names = _get_index_names(db.engine, "posts")
        assert "ix_posts_created_at" in names, (
            f"Expected index 'ix_posts_created_at' on posts, found: {names}"
        )


def test_ix_posts_created_at_covers_correct_column(app, db):
    """ix_posts_created_at must cover the created_at column."""
    with app.app_context():
        indexed = _get_indexed_columns(db.engine, "posts")
        assert indexed.get("ix_posts_created_at") == {"created_at"}, (
            f"ix_posts_created_at covers wrong columns: {indexed.get('ix_posts_created_at')}"
        )


# ---------------------------------------------------------------------------
# comments table — required indexes
# ---------------------------------------------------------------------------

def test_ix_comments_post_id_exists(app, db):
    """ix_comments_post_id must exist on the comments table."""
    with app.app_context():
        names = _get_index_names(db.engine, "comments")
        assert "ix_comments_post_id" in names, (
            f"Expected index 'ix_comments_post_id' on comments, found: {names}"
        )


def test_ix_comments_post_id_covers_correct_column(app, db):
    """ix_comments_post_id must cover the post_id column."""
    with app.app_context():
        indexed = _get_indexed_columns(db.engine, "comments")
        assert indexed.get("ix_comments_post_id") == {"post_id"}, (
            f"ix_comments_post_id covers wrong columns: {indexed.get('ix_comments_post_id')}"
        )


# ---------------------------------------------------------------------------
# posts table — indexes that must NOT exist
# ---------------------------------------------------------------------------

def test_no_explicit_index_on_posts_author_id(app, db):
    """posts.author_id must not have an explicit named index.

    Current queries do not filter or join on author_id in isolation, so adding
    an index would be premature and wastes write overhead.
    """
    with app.app_context():
        indexed = _get_indexed_columns(db.engine, "posts")
        for idx_name, cols in indexed.items():
            if cols == {"author_id"}:
                assert False, (
                    f"Unexpected explicit index '{idx_name}' on posts.author_id"
                )


# ---------------------------------------------------------------------------
# comments table — indexes that must NOT exist
# ---------------------------------------------------------------------------

def test_no_explicit_index_on_comments_author_id(app, db):
    """comments.author_id must not have an explicit named index.

    No current query filters comments by author_id, so this index is not
    justified.
    """
    with app.app_context():
        indexed = _get_indexed_columns(db.engine, "comments")
        for idx_name, cols in indexed.items():
            if cols == {"author_id"}:
                assert False, (
                    f"Unexpected explicit index '{idx_name}' on comments.author_id"
                )


# ---------------------------------------------------------------------------
# No duplicate single-column indexes on the same column
# ---------------------------------------------------------------------------

def test_no_duplicate_indexes_on_posts(app, db):
    """No two indexes on the posts table should cover the exact same set of columns."""
    with app.app_context():
        inspector = inspect(db.engine)
        seen: dict[frozenset, str] = {}
        for idx in inspector.get_indexes("posts"):
            key = frozenset(idx["column_names"])
            prev = seen.get(key)
            assert prev is None, (
                f"Duplicate indexes on posts covering {set(key)}: "
                f"'{prev}' and '{idx['name']}'"
            )
            seen[key] = idx["name"]


def test_no_duplicate_indexes_on_comments(app, db):
    """No two indexes on the comments table should cover the exact same set of columns."""
    with app.app_context():
        inspector = inspect(db.engine)
        seen: dict[frozenset, str] = {}
        for idx in inspector.get_indexes("comments"):
            key = frozenset(idx["column_names"])
            prev = seen.get(key)
            assert prev is None, (
                f"Duplicate indexes on comments covering {set(key)}: "
                f"'{prev}' and '{idx['name']}'"
            )
            seen[key] = idx["name"]

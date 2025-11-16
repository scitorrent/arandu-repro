"""Tests for paper migrations."""

import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="function")
def alembic_cfg():
    """Create Alembic config for testing."""
    cfg = Config("alembic.ini")
    return cfg


@pytest.fixture(scope="function")
def test_db_engine():
    """Create database engine for migration testing.
    
    Uses PostgreSQL if DATABASE_URL is set, otherwise falls back to SQLite.
    Note: Some migrations (ENUMs, CHECK constraints) require PostgreSQL.
    """
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Use PostgreSQL from environment (CI)
        engine = create_engine(database_url)
    else:
        # Fallback to SQLite for local testing
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return engine


def test_papers_table_created(test_db_engine, alembic_cfg):
    """Test that papers table is created."""
    # Set database URL from engine
    database_url = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    # Run migrations up to papers
    with test_db_engine.connect() as connection:
        alembic_cfg.attributes["connection"] = connection
        command.upgrade(alembic_cfg, "a1b2c3d4e5f6")

    inspector = inspect(test_db_engine)
    tables = inspector.get_table_names()

    assert "papers" in tables

    # Check columns
    columns = [col["name"] for col in inspector.get_columns("papers")]
    assert "id" in columns
    assert "aid" in columns
    assert "visibility" in columns
    assert "deleted_at" in columns


def test_paper_versions_table_created(test_db_engine, alembic_cfg):
    """Test that paper_versions table is created."""
    database_url = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    with test_db_engine.connect() as connection:
        alembic_cfg.attributes["connection"] = connection
        command.upgrade(alembic_cfg, "b2c3d4e5f6a7")

    inspector = inspect(test_db_engine)
    assert "paper_versions" in inspector.get_table_names()

    columns = [col["name"] for col in inspector.get_columns("paper_versions")]
    assert "aid" in columns
    assert "version" in columns
    assert "pdf_path" in columns


def test_paper_external_ids_table_created(test_db_engine, alembic_cfg):
    """Test that paper_external_ids table is created."""
    database_url = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    with test_db_engine.connect() as connection:
        alembic_cfg.attributes["connection"] = connection
        command.upgrade(alembic_cfg, "c3d4e5f6a7b8")

    inspector = inspect(test_db_engine)
    assert "paper_external_ids" in inspector.get_table_names()


def test_quality_scores_table_created(test_db_engine, alembic_cfg):
    """Test that quality_scores table is created."""
    database_url = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    with test_db_engine.connect() as connection:
        alembic_cfg.attributes["connection"] = connection
        command.upgrade(alembic_cfg, "d4e5f6a7b8c9")

    inspector = inspect(test_db_engine)
    assert "quality_scores" in inspector.get_table_names()

    columns = [col["name"] for col in inspector.get_columns("quality_scores")]
    assert "scope" in columns
    assert "paper_id" in columns
    assert "paper_version_id" in columns


def test_claims_table_created(test_db_engine, alembic_cfg):
    """Test that claims table is created."""
    database_url = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    with test_db_engine.connect() as connection:
        alembic_cfg.attributes["connection"] = connection
        command.upgrade(alembic_cfg, "e5f6a7b8c9d0")

    inspector = inspect(test_db_engine)
    assert "claims" in inspector.get_table_names()

    columns = [col["name"] for col in inspector.get_columns("claims")]
    assert "paper_version_id" in columns
    assert "hash" in columns
    assert "text" in columns


def test_claim_links_table_created(test_db_engine, alembic_cfg):
    """Test that claim_links table is created."""
    database_url = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    with test_db_engine.connect() as connection:
        alembic_cfg.attributes["connection"] = connection
        command.upgrade(alembic_cfg, "f6a7b8c9d0e1")

    inspector = inspect(test_db_engine)
    assert "claim_links" in inspector.get_table_names()

    columns = [col["name"] for col in inspector.get_columns("claim_links")]
    assert "relation" in columns
    assert "confidence" in columns
    assert "reasoning_ref" in columns


def test_all_migrations_reversible(test_db_engine, alembic_cfg):
    """Test that all migrations can be reversed."""
    database_url = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    with test_db_engine.connect() as connection:
        alembic_cfg.attributes["connection"] = connection
        # Upgrade to latest
        command.upgrade(alembic_cfg, "head")

        inspector = inspect(test_db_engine)

        # Downgrade to base
        command.downgrade(alembic_cfg, "dec04362e66d")

        inspector = inspect(test_db_engine)
        tables_after = set(inspector.get_table_names())

        # Should have removed paper-related tables
        paper_tables = {"papers", "paper_versions", "paper_external_ids", "quality_scores", "claims", "claim_links"}
        assert not paper_tables.intersection(tables_after)


def test_foreign_keys(test_db_engine, alembic_cfg):
    """Test that foreign keys are created correctly."""
    alembic_cfg.set_main_option("sqlalchemy.url", "sqlite:///:memory:")

    with test_db_engine.connect() as connection:
        alembic_cfg.attributes["connection"] = connection
        command.upgrade(alembic_cfg, "head")

    inspector = inspect(test_db_engine)

    # Check paper_versions FK to papers
    fks = inspector.get_foreign_keys("paper_versions")
    assert any(fk["referred_table"] == "papers" for fk in fks)

    # Check claims FK to paper_versions
    fks = inspector.get_foreign_keys("claims")
    assert any(fk["referred_table"] == "paper_versions" for fk in fks)

    # Check claim_links FK to claims
    fks = inspector.get_foreign_keys("claim_links")
    assert any(fk["referred_table"] == "claims" for fk in fks)


def test_indexes(test_db_engine, alembic_cfg):
    """Test that indexes are created."""
    database_url = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    with test_db_engine.connect() as connection:
        alembic_cfg.attributes["connection"] = connection
        command.upgrade(alembic_cfg, "head")

    inspector = inspect(test_db_engine)

    # Check papers indexes
    indexes = [idx["name"] for idx in inspector.get_indexes("papers")]
    assert any("aid" in idx for idx in indexes)
    assert any("visibility" in idx for idx in indexes)

    # Check claims indexes
    indexes = [idx["name"] for idx in inspector.get_indexes("claims")]
    assert any("hash" in idx for idx in indexes)
    assert any("paper_version_id" in idx for idx in indexes)


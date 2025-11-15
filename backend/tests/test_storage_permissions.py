"""Tests for storage permissions and PAPERS_BASE."""

import pytest
import tempfile
import shutil
from pathlib import Path

from app.config import settings
from app.utils.storage import (
    validate_papers_base,
    get_paper_version_path,
    ensure_paper_version_directory,
    generate_secure_aid,
)


def test_validate_papers_base():
    """Test PAPERS_BASE validation and creation."""
    # Should create directory if it doesn't exist
    base = validate_papers_base()
    
    assert base.exists()
    assert base.is_dir()
    assert base.is_absolute()
    
    # Check write permissions
    test_file = base / ".test_write"
    test_file.write_text("test")
    assert test_file.exists()
    test_file.unlink()


def test_get_paper_version_path():
    """Test paper version path generation."""
    aid = "test-paper-001"
    version = 1
    filename = "file.pdf"
    
    path = get_paper_version_path(aid, version, filename)
    
    assert str(path) == f"papers/{aid}/v{version}/{filename}"
    assert ".." not in str(path)
    assert "/" not in filename or filename == "file.pdf"
    
    # Test path traversal protection
    with pytest.raises(ValueError, match="Invalid filename"):
        get_paper_version_path(aid, version, "../../../etc/passwd")
    
    with pytest.raises(ValueError, match="Invalid AID format"):
        get_paper_version_path("../../../etc", version, filename)
    
    with pytest.raises(ValueError, match="Version must be >= 1"):
        get_paper_version_path(aid, 0, filename)


def test_ensure_paper_version_directory():
    """Test paper version directory creation."""
    aid = generate_secure_aid()
    version = 1
    
    # Create directory
    full_path = ensure_paper_version_directory(aid, version)
    
    assert full_path.parent.exists()
    assert full_path.parent.is_dir()
    
    # Verify path structure
    assert aid in str(full_path)
    assert f"v{version}" in str(full_path)
    
    # Test write permissions
    test_file = full_path.parent / "test.txt"
    test_file.write_text("test")
    assert test_file.exists()
    test_file.unlink()
    
    # Cleanup
    shutil.rmtree(full_path.parent.parent, ignore_errors=True)


def test_papers_base_quota_and_permissions():
    """Test PAPERS_BASE quota and permissions (create/delete cycle)."""
    base = validate_papers_base()
    
    # Generate test AID
    aid = generate_secure_aid()
    version = 1
    
    # Create directory structure
    paper_dir = base / "papers" / aid / f"v{version}"
    paper_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test file
    test_file = paper_dir / "test.pdf"
    test_content = b"PDF test content" * 1000  # ~16KB
    test_file.write_bytes(test_content)
    
    # Verify file exists and is readable
    assert test_file.exists()
    assert test_file.stat().st_size > 0
    
    # Verify we can read it
    content = test_file.read_bytes()
    assert len(content) == len(test_content)
    
    # Delete file
    test_file.unlink()
    assert not test_file.exists()
    
    # Delete directory
    paper_dir.rmdir()
    assert not paper_dir.exists()
    
    # Cleanup parent directories if empty
    try:
        (paper_dir.parent).rmdir()  # v{version} parent
        (paper_dir.parent.parent).rmdir()  # {aid} parent
    except OSError:
        pass  # Directory not empty or doesn't exist


def test_concurrent_directory_creation():
    """Test concurrent directory creation (atomicity)."""
    import threading
    import time
    
    base = validate_papers_base()
    aid = generate_secure_aid()
    version = 1
    
    created_paths = []
    errors = []
    lock = threading.Lock()
    
    def create_dir():
        try:
            path = ensure_paper_version_directory(aid, version)
            with lock:
                created_paths.append(path)
        except Exception as e:
            with lock:
                errors.append(str(e))
    
    # Create directories concurrently
    threads = [threading.Thread(target=create_dir) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # All should succeed (directory creation is idempotent)
    assert len(errors) == 0, f"Errors: {errors}"
    assert len(created_paths) == 5
    
    # All paths should be the same (normalize paths)
    normalized_paths = [str(p.resolve()) for p in created_paths]
    assert len(set(normalized_paths)) == 1, f"Paths differ: {set(normalized_paths)}"
    
    # Cleanup
    if created_paths:
        try:
            # Remove up to papers/{aid}
            cleanup_path = created_paths[0].parent.parent
            if cleanup_path.exists():
                shutil.rmtree(cleanup_path, ignore_errors=True)
        except Exception:
            pass  # Ignore cleanup errors


def test_papers_base_config():
    """Test PAPERS_BASE configuration."""
    assert hasattr(settings, 'papers_base_path')
    assert settings.papers_base_path is not None
    
    # Should be a Path object
    assert isinstance(settings.papers_base_path, Path)
    
    # Should be absolute
    assert settings.papers_base_path.is_absolute()


def test_generate_secure_aid():
    """Test secure AID generation."""
    aid1 = generate_secure_aid()
    aid2 = generate_secure_aid()
    
    # Should be different
    assert aid1 != aid2
    
    # Should be URL-safe (alphanumeric, dash, underscore)
    assert all(c.isalnum() or c in ('-', '_') for c in aid1)
    assert all(c.isalnum() or c in ('-', '_') for c in aid2)
    
    # Default length
    assert len(aid1) == 12
    assert len(aid2) == 12
    
    # Custom length
    aid3 = generate_secure_aid(length=20)
    assert len(aid3) == 20


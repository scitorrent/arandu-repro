"""Tests for checklist generator."""



from app.worker.checklist_generator import (
    Checklist,
    check_comparatives,
    check_data_available,
    check_environment_files,
    check_license,
    check_metrics_defined,
    check_seeds_fixed,
    generate_checklist,
)


def test_check_data_available_with_link():
    """Test data availability check with link in paper."""
    text = "The dataset is available at https://example.com/data"
    item = check_data_available(text)
    assert item.status in ("ok", "partial")
    assert item.evidence is not None


def test_check_seeds_fixed_with_mention():
    """Test seed check with seed mention in paper."""
    text = "We set random_seed = 42 for reproducibility."
    item = check_seeds_fixed(text)
    assert item.status in ("ok", "partial")
    assert item.evidence is not None


def test_check_environment_files_found(tmp_path):
    """Test environment files check when files exist."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()
    (repo_path / "requirements.txt").write_text("numpy==1.24.0\n")

    item = check_environment_files(repo_path)
    assert item.status == "ok"
    assert "requirements.txt" in item.evidence


def test_check_environment_files_missing(tmp_path):
    """Test environment files check when no files exist."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()

    item = check_environment_files(repo_path)
    assert item.status == "missing"


def test_check_metrics_defined():
    """Test metrics check."""
    text = "We report accuracy and F1-score."
    item = check_metrics_defined(text)
    assert item.status == "ok"
    assert item.evidence is not None


def test_check_comparatives():
    """Test comparatives check."""
    text = "We compare our method to BERT baseline."
    item = check_comparatives(text)
    assert item.status in ("ok", "partial")


def test_check_license_found(tmp_path):
    """Test license check when LICENSE file exists."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()
    (repo_path / "LICENSE").write_text("MIT License")

    item = check_license(repo_path)
    assert item.status == "ok"
    assert "LICENSE" in item.evidence


def test_generate_checklist():
    """Test complete checklist generation."""
    paper_text = """
    We use the dataset available at https://example.com/data.
    We set random_seed = 42.
    We report accuracy and F1-score.
    We compare to BERT baseline.
    """
    from app.worker.claim_extractor import Claim

    claims = [
        Claim(
            id="c1",
            text="Our method achieves 95% accuracy",
            section="results",
            spans=[[0, 30]],
        )
    ]

    checklist = generate_checklist(paper_text, claims)
    assert isinstance(checklist, Checklist)
    assert len(checklist.items) > 0
    assert checklist.summary is not None

    # Should have at least some OK items
    ok_items = [item for item in checklist.items if item.status == "ok"]
    assert len(ok_items) > 0


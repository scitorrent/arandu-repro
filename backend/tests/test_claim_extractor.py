"""Tests for claim extraction."""

import pytest

from app.worker.claim_extractor import (
    Claim,
    _split_sentences,
    claims_to_json,
    extract_claims_baseline,
    extract_claims_by_section,
)


def test_split_sentences():
    """Test sentence splitting."""
    text = "First sentence. Second sentence! Third sentence?"
    sentences = _split_sentences(text)
    assert len(sentences) >= 3
    assert "First sentence" in sentences[0]
    assert "Second sentence" in sentences[1]


def test_extract_claims_baseline_we_show():
    """Test claim extraction with 'we show' pattern."""
    text = "We show that our method achieves state-of-the-art results."
    claims = extract_claims_baseline(text)
    assert len(claims) > 0
    assert any("show" in claim.text.lower() for claim in claims)


def test_extract_claims_baseline_outperforms():
    """Test claim extraction with 'outperforms' pattern."""
    text = "Our approach significantly outperforms previous methods."
    claims = extract_claims_baseline(text)
    assert len(claims) > 0
    assert any("outperforms" in claim.text.lower() for claim in claims)


def test_extract_claims_baseline_confidence():
    """Test that claims have confidence scores."""
    text = "Our method achieves superior results. We demonstrate this."
    claims = extract_claims_baseline(text)
    assert len(claims) > 0
    for claim in claims:
        assert 0.0 <= claim.confidence <= 1.0


def test_extract_claims_by_section():
    """Test claim extraction by section."""
    text = """
    Introduction
    This paper introduces a new method.

    Results
    We show that our method achieves 95% accuracy.
    Our approach significantly outperforms baselines.
    """
    claims = extract_claims_by_section(text)
    assert len(claims) > 0
    # Should extract claims from results section
    result_claims = [c for c in claims if c.section == "results"]
    assert len(result_claims) > 0


def test_claims_to_json():
    """Test claims to JSON conversion."""
    claims = [
        Claim(
            id="c1",
            text="Test claim",
            section="results",
            spans=[[0, 10]],
            confidence=0.8,
        )
    ]
    json_data = claims_to_json(claims)
    assert len(json_data) == 1
    assert json_data[0]["id"] == "c1"
    assert json_data[0]["text"] == "Test claim"
    assert json_data[0]["section"] == "results"
    assert json_data[0]["confidence"] == 0.8


def test_extract_claims_minimum_length():
    """Test that very short sentences are skipped."""
    text = "Hi. This is a very short sentence. We demonstrate significant improvements."
    claims = extract_claims_baseline(text)
    # Should skip "Hi" and "This is a very short sentence"
    assert len(claims) >= 1
    assert all(len(claim.text) >= 20 for claim in claims)


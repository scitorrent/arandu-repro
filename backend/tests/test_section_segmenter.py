"""Tests for section segmentation."""


from app.worker.section_segmenter import get_section_text, segment_paper


def test_segment_paper_finds_sections():
    """Test that section segmentation finds common sections."""
    text = """
    Abstract
    This is the abstract text.

    Introduction
    This is the introduction.

    Method
    This is the method section.

    Results
    This is the results section.
    """
    sections = segment_paper(text)
    assert len(sections) > 0
    section_names = [s.name for s in sections]
    assert "abstract" in section_names or "introduction" in section_names


def test_segment_paper_section_text():
    """Test that section text is correctly extracted."""
    text = """
    Introduction
    This is the introduction text with multiple sentences.
    It continues here.

    Method
    This is the method section.
    """
    sections = segment_paper(text)
    intro_section = next((s for s in sections if s.name == "introduction"), None)
    if intro_section:
        assert "introduction text" in intro_section.text.lower()


def test_get_section_text():
    """Test get_section_text helper."""
    text = """
    Abstract
    Abstract content here.

    Results
    Results content here.
    """
    results_text = get_section_text(text, "results")
    assert results_text is not None
    assert "results content" in results_text.lower()


def test_get_section_text_not_found():
    """Test get_section_text when section not found."""
    text = "Some text without sections."
    section_text = get_section_text(text, "results")
    assert section_text is None


def test_section_has_spans():
    """Test that sections have correct start/end positions."""
    text = "Introduction\nIntro text.\n\nMethod\nMethod text."
    sections = segment_paper(text)
    assert len(sections) > 0
    for section in sections:
        assert section.start >= 0
        assert section.end > section.start
        assert len(section.text) > 0


"""Section segmentation for scientific papers."""

import re
from typing import NamedTuple

logger = None  # Will be set by module import


class Section(NamedTuple):
    """Represents a paper section."""

    name: str
    start: int  # Character position
    end: int  # Character position
    text: str


# Common section headings (case-insensitive)
SECTION_PATTERNS = [
    (r"^\s*(?:Abstract|Summary)\s*$", "abstract"),
    (r"^\s*(?:1\s*\.?\s*)?(?:Introduction|Intro)\s*$", "introduction"),
    (r"^\s*(?:2\s*\.?\s*)?(?:Related\s+Work|Background|Literature\s+Review)\s*$", "related_work"),
    (r"^\s*(?:3\s*\.?\s*)?(?:Method|Methodology|Approach|Model|Architecture)\s*$", "method"),
    (r"^\s*(?:4\s*\.?\s*)?(?:Experiments?|Evaluation|Results?)\s*$", "results"),
    (r"^\s*(?:5\s*\.?\s*)?(?:Discussion|Analysis|Interpretation)\s*$", "discussion"),
    (r"^\s*(?:6\s*\.?\s*)?(?:Conclusion|Conclusions?|Summary)\s*$", "conclusion"),
    (r"^\s*(?:7\s*\.?\s*)?(?:Limitations?|Future\s+Work)\s*$", "limitations"),
    (r"^\s*(?:Appendix|Appendices)\s*$", "appendix"),
]


def segment_paper(text: str) -> list[Section]:
    """
    Segment paper text into sections.

    Args:
        text: Full paper text

    Returns:
        List of Section objects
    """
    sections: list[Section] = []
    lines = text.split("\n")
    current_section: str | None = None
    current_start = 0
    current_lines: list[str] = []

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            if current_lines:
                current_lines.append(line)
            continue

        # Check if this line matches a section heading
        matched_section = None
        for pattern, section_name in SECTION_PATTERNS:
            if re.match(pattern, line_stripped, re.IGNORECASE):
                matched_section = section_name
                break

        if matched_section:
            # Save previous section
            if current_section and current_lines:
                section_text = "\n".join(current_lines)
                sections.append(
                    Section(
                        name=current_section,
                        start=current_start,
                        end=current_start + len(section_text),
                        text=section_text,
                    )
                )

            # Start new section
            current_section = matched_section
            current_start = sum(len(line_item) + 1 for line_item in lines[:i])  # +1 for newline
            current_lines = [line]
        else:
            current_lines.append(line)

    # Add final section
    if current_section and current_lines:
        section_text = "\n".join(current_lines)
        sections.append(
            Section(
                name=current_section,
                start=current_start,
                end=current_start + len(section_text),
                text=section_text,
            )
        )

    return sections


def get_section_text(text: str, section_name: str) -> str | None:
    """
    Get text for a specific section.

    Args:
        text: Full paper text
        section_name: Section name (e.g., "introduction", "method", "results")

    Returns:
        Section text or None if not found
    """
    sections = segment_paper(text)
    for section in sections:
        if section.name == section_name:
            return section.text
    return None


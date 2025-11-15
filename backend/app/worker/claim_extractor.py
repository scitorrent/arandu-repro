"""Claim extraction from paper text."""

import logging
import re
from dataclasses import dataclass
from typing import Any

from app.worker.section_segmenter import get_section_text, segment_paper

logger = logging.getLogger(__name__)


@dataclass
class Claim:
    """Represents a claim extracted from paper."""

    id: str
    text: str
    section: str | None  # Section name (introduction, method, results, etc.)
    spans: list[list[int]]  # Character spans [[start, end], ...] in original text
    confidence: float = 0.0  # Confidence score (0-1)


# Claim patterns (baseline deterministic extraction)
CLAIM_PATTERNS = [
    (r"\b(?:we|our|this|the)\s+(?:show|demonstrate|prove|establish|find|observe|propose|introduce|present|develop)\b", 0.7),
    (r"\b(?:our|this|the)\s+(?:method|approach|model|system|framework|algorithm)\s+(?:achieves|obtains|yields|produces|improves)\b", 0.8),
    (r"\b(?:state-of-the-art|SOTA|best|superior|outperforms|beats)\b", 0.6),
    (r"\b(?:significantly|substantially|considerably)\s+(?:improves?|outperforms?|better)\b", 0.7),
    (r"\b(?:we|our)\s+(?:results?|experiments?|evaluation)\s+(?:show|demonstrate|indicate|suggest)\b", 0.7),
    (r"\b(?:we|our)\s+(?:contribution|contribution|novelty)\b", 0.6),
]


def extract_claims_baseline(text: str, section_name: str | None = None) -> list[Claim]:
    """
    Extract claims using baseline deterministic patterns.

    Args:
        text: Paper text or section text
        section_name: Optional section name for context

    Returns:
        List of Claim objects
    """
    claims: list[Claim] = []
    sentences = _split_sentences(text)

    claim_id = 0
    for sentence in sentences:
        sentence_stripped = sentence.strip()
        if len(sentence_stripped) < 20:  # Skip very short sentences
            continue

        # Check for claim patterns
        best_match = None
        best_confidence = 0.0

        for pattern, confidence in CLAIM_PATTERNS:
            if re.search(pattern, sentence_stripped, re.IGNORECASE):
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = pattern

        if best_match:
            # Find position in original text
            start = text.find(sentence_stripped)
            end = start + len(sentence_stripped) if start >= 0 else 0

            claim = Claim(
                id=f"c{claim_id}",
                text=sentence_stripped,
                section=section_name,
                spans=[[start, end]] if start >= 0 else [],
                confidence=best_confidence,
            )
            claims.append(claim)
            claim_id += 1

    return claims


def extract_claims_by_section(text: str) -> list[Claim]:
    """
    Extract claims from paper, segmented by section.

    Args:
        text: Full paper text

    Returns:
        List of Claim objects with section information
    """
    all_claims: list[Claim] = []

    # Get sections
    sections = segment_paper(text)
    if not sections:
        # Fallback: extract from full text
        return extract_claims_baseline(text)

    # Extract claims from each section
    for section in sections:
        # Focus on results, discussion, conclusion for claims
        if section.name in ("results", "discussion", "conclusion", "introduction"):
            section_claims = extract_claims_baseline(section.text, section.name)
            all_claims.extend(section_claims)

    # Remove duplicates (same text)
    seen_texts = set()
    unique_claims = []
    for claim in all_claims:
        text_key = claim.text.lower().strip()[:100]  # First 100 chars as key
        if text_key not in seen_texts:
            seen_texts.add(text_key)
            unique_claims.append(claim)

    return unique_claims


def _split_sentences(text: str) -> list[str]:
    """
    Split text into sentences.

    Simple sentence splitting (can be enhanced with NLTK/spaCy).

    Args:
        text: Text to split

    Returns:
        List of sentences
    """
    # Simple sentence splitting by period, exclamation, question mark
    # (handles common abbreviations)
    sentence_endings = re.compile(r"([.!?])\s+")
    sentences = sentence_endings.split(text)

    result = []
    for i in range(0, len(sentences) - 1, 2):
        if i + 1 < len(sentences):
            sentence = sentences[i] + sentences[i + 1]
            result.append(sentence.strip())
        else:
            result.append(sentences[i].strip())

    # Add last sentence if exists
    if len(sentences) % 2 == 1:
        result.append(sentences[-1].strip())

    return [s for s in result if s]


def claims_to_json(claims: list[Claim]) -> list[dict[str, Any]]:
    """
    Convert claims to JSON-serializable format.

    Args:
        claims: List of Claim objects

    Returns:
        List of dictionaries
    """
    return [
        {
            "id": claim.id,
            "text": claim.text,
            "section": claim.section,
            "spans": claim.spans,
            "confidence": claim.confidence,
        }
        for claim in claims
    ]


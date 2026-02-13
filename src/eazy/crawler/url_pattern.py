"""URL pattern classification and normalization.

URL 경로 세그먼트를 분석하여 동적 파라미터 타입을 식별한다.
분류 우선순위: uuid → int → date → hash → slug (PRD 명시).
"""

from __future__ import annotations

import re

from eazy.models.crawl_types import SegmentType

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}"
    r"-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
_INT_RE = re.compile(r"^\d+$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_HASH_RE = re.compile(
    r"^[0-9a-f]{32}$|^[0-9a-f]{40}$|^[0-9a-f]{64}$",
    re.IGNORECASE,
)
_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)+$")


def classify_segment(segment: str) -> SegmentType | None:
    """Classify a URL path segment into a dynamic type.

    Checks the segment against known patterns in priority order:
    uuid → int → date → hash → slug. Returns None for literal
    (static) segments that don't match any dynamic pattern.

    Args:
        segment: A single URL path segment to classify.

    Returns:
        The matching SegmentSingleType, or None if the segment
        is a static literal.
    """
    if not segment:
        return None

    if _UUID_RE.match(segment):
        return SegmentType.UUID

    if _INT_RE.match(segment):
        return SegmentType.INT

    if _DATE_RE.match(segment):
        return SegmentType.DATE

    if _HASH_RE.match(segment):
        return SegmentType.HASH

    if _SLUG_RE.match(segment):
        return SegmentType.SLUG

    return None

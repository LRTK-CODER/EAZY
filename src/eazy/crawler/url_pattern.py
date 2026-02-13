"""URL pattern classification and normalization.

URL 경로 세그먼트를 분석하여 동적 파라미터 타입을 식별한다.
분류 우선순위: uuid → int → date → hash → slug (PRD 명시).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from eazy.models.crawl_types import (
    PatternGroup,
    PatternNormalizationResult,
    SegmentType,
    URLPattern,
)

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


@dataclass
class _PatternTracker:
    """Internal tracker for a single URL pattern group."""

    scheme: str
    netloc: str
    structural_key: tuple[str, ...]
    segment_types: list[SegmentType | None]
    sample_urls: list[str] = field(default_factory=list)
    total_count: int = 0
    max_samples: int = 3


def _promote_type(
    existing: SegmentType | None,
    incoming: SegmentType | None,
) -> SegmentType | None:
    """Promote two segment types to a common supertype.

    Args:
        existing: Current type at the position.
        incoming: New type from the incoming URL.

    Returns:
        The promoted type, or STRING if types differ.
    """
    if existing is None or incoming is None:
        return existing or incoming
    if existing == incoming:
        return existing
    return SegmentType.STRING


def _build_pattern_path(
    segments: list[str],
    types: list[SegmentType | None],
) -> str:
    """Build a pattern path string from segments and types.

    Args:
        segments: Raw path segments.
        types: Classified type per segment (None = literal).

    Returns:
        Pattern path like ``/users/<int>/posts/<slug>``.
    """
    if not segments:
        return "/"
    parts: list[str] = []
    for seg, seg_type in zip(segments, types):
        if seg_type is not None:
            parts.append(f"<{seg_type.value}>")
        else:
            parts.append(seg)
    return "/" + "/".join(parts)


class URLPatternNormalizer:
    """Normalize URLs to patterns and group by structure.

    Classifies each path segment, replaces dynamic segments with
    type placeholders, groups URLs by structural pattern, handles
    type promotion for mixed types, and controls sampling.

    Args:
        max_samples: Maximum sample URLs to keep per pattern group.
    """

    def __init__(self, max_samples: int = 3) -> None:
        self._max_samples = max_samples
        self._trackers: dict[tuple[str, str, tuple[str, ...]], _PatternTracker] = {}
        self._total_processed: int = 0
        self._total_skipped: int = 0

    def _parse_and_classify(
        self, url: str
    ) -> tuple[str, str, list[str], list[SegmentType | None]]:
        """Parse a URL and classify each path segment.

        Args:
            url: Full URL string.

        Returns:
            Tuple of (scheme, netloc, segments, types).
        """
        parsed = urlparse(url)
        segments = [s for s in parsed.path.split("/") if s]
        types = [classify_segment(s) for s in segments]
        return parsed.scheme, parsed.netloc, segments, types

    @staticmethod
    def _compute_structural_key(
        segments: list[str],
        types: list[SegmentType | None],
    ) -> tuple[str, ...]:
        """Compute a hashable structural key for grouping.

        Literal segments keep their value; dynamic segments
        become ``"*"``.

        Args:
            segments: Raw path segments.
            types: Classified type per segment.

        Returns:
            Tuple of strings usable as a dict key.
        """
        return tuple("*" if t is not None else s for s, t in zip(segments, types))

    def normalize_url_to_pattern(self, url: str) -> URLPattern:
        """Normalize a single URL into a URLPattern.

        Args:
            url: Full URL string to normalize.

        Returns:
            A URLPattern with dynamic segments replaced by
            type placeholders.
        """
        scheme, netloc, segments, types = self._parse_and_classify(url)
        dynamic_types = tuple(t for t in types if t is not None)
        pattern_path = _build_pattern_path(segments, types)
        return URLPattern(
            scheme=scheme,
            netloc=netloc,
            pattern_path=pattern_path,
            segment_types=dynamic_types,
        )

    def add_url(self, url: str) -> bool:
        """Add a URL and return whether it was sampled.

        Args:
            url: Full URL string to add.

        Returns:
            True if the URL was added as a sample, False if the
            pattern's sample limit was already reached.
        """
        self._total_processed += 1
        scheme, netloc, segments, types = self._parse_and_classify(url)
        key = (
            scheme,
            netloc,
            self._compute_structural_key(segments, types),
        )

        tracker = self._trackers.get(key)
        if tracker is None:
            tracker = _PatternTracker(
                scheme=scheme,
                netloc=netloc,
                structural_key=key[2],
                segment_types=list(types),
                max_samples=self._max_samples,
            )
            tracker.sample_urls.append(url)
            tracker.total_count = 1
            self._trackers[key] = tracker
            return True

        # Type promotion per dynamic position
        for i, incoming_type in enumerate(types):
            tracker.segment_types[i] = _promote_type(
                tracker.segment_types[i], incoming_type
            )

        tracker.total_count += 1
        if len(tracker.sample_urls) < tracker.max_samples:
            tracker.sample_urls.append(url)
            return True

        self._total_skipped += 1
        return False

    def should_skip(self, url: str) -> bool:
        """Check if a URL's pattern has reached its sample limit.

        Args:
            url: Full URL string to check.

        Returns:
            True if the pattern is already at max samples.
        """
        scheme, netloc, segments, types = self._parse_and_classify(url)
        key = (
            scheme,
            netloc,
            self._compute_structural_key(segments, types),
        )
        tracker = self._trackers.get(key)
        if tracker is None:
            return False
        return len(tracker.sample_urls) >= tracker.max_samples

    def get_results(self) -> PatternNormalizationResult:
        """Build the final normalization result.

        Returns:
            PatternNormalizationResult with all groups and
            aggregate statistics.
        """
        groups: list[PatternGroup] = []
        for tracker in self._trackers.values():
            dynamic_types = tuple(t for t in tracker.segment_types if t is not None)
            # Rebuild segments from structural key with
            # promoted types
            seg_parts = list(tracker.structural_key)
            pattern_path = _build_pattern_path(seg_parts, tracker.segment_types)
            pattern = URLPattern(
                scheme=tracker.scheme,
                netloc=tracker.netloc,
                pattern_path=pattern_path,
                segment_types=dynamic_types,
            )
            groups.append(
                PatternGroup(
                    pattern=pattern,
                    sample_urls=list(tracker.sample_urls),
                    total_count=tracker.total_count,
                    max_samples=tracker.max_samples,
                )
            )
        return PatternNormalizationResult(
            groups=groups,
            total_urls_processed=self._total_processed,
            total_patterns_found=len(groups),
            total_urls_skipped=self._total_skipped,
        )

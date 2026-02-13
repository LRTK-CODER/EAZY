"""Unit tests for URL pattern classification."""

from eazy.crawler.url_pattern import classify_segment
from eazy.models.crawl_types import SegmentType


class TestClassifySegment:
    """Tests for classify_segment function."""

    # --- UUID ---

    def test_uuid_v4_lowercase(self):
        """Lowercase UUID v4 should return SegmentType.UUID."""
        result = classify_segment("550e8400-e29b-41d4-a716-446655440000")
        assert result == SegmentType.UUID

    def test_uuid_v4_uppercase(self):
        """Uppercase UUID v4 should return SegmentType.UUID."""
        result = classify_segment("550E8400-E29B-41D4-A716-446655440000")
        assert result == SegmentType.UUID

    # --- INT ---

    def test_pure_digits(self):
        """Pure digit string should return SegmentType.INT."""
        assert classify_segment("12345") == SegmentType.INT

    def test_single_digit(self):
        """Single digit should return SegmentType.INT."""
        assert classify_segment("0") == SegmentType.INT

    def test_zero(self):
        """Zero string should return SegmentType.INT."""
        assert classify_segment("0") == SegmentType.INT

    # --- DATE ---

    def test_date_yyyy_mm_dd(self):
        """ISO date format should return SegmentType.DATE."""
        assert classify_segment("2024-01-15") == SegmentType.DATE

    # --- HASH ---

    def test_md5_32_hex(self):
        """32-char hex string (MD5) should return SegmentType.HASH."""
        assert classify_segment("d41d8cd98f00b204e9800998ecf8427e") == SegmentType.HASH

    def test_sha1_40_hex(self):
        """40-char hex string (SHA-1) should return SegmentType.HASH."""
        assert (
            classify_segment("da39a3ee5e6b4b0d3255bfef95601890afd80709")
            == SegmentType.HASH
        )

    def test_sha256_64_hex(self):
        """64-char hex string (SHA-256) should return SegmentType.HASH."""
        seg = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert classify_segment(seg) == SegmentType.HASH

    # --- SLUG ---

    def test_slug_lowercase_hyphens(self):
        """Lowercase hyphenated string should return SegmentType.SLUG."""
        assert classify_segment("my-first-post") == SegmentType.SLUG

    def test_slug_with_numbers(self):
        """Slug with numbers should return SegmentType.SLUG."""
        assert classify_segment("post-123-title") == SegmentType.SLUG

    # --- None (literal segments) ---

    def test_plain_text_returns_none(self):
        """Plain text without special pattern should return None."""
        assert classify_segment("users") is None

    def test_mixed_case_returns_none(self):
        """Mixed case word should return None."""
        assert classify_segment("Users") is None

    def test_empty_string_returns_none(self):
        """Empty string should return None."""
        assert classify_segment("") is None

    # --- Priority tests ---

    def test_uuid_before_hash(self):
        """UUID should match before hash even though it's hex."""
        result = classify_segment("550e8400-e29b-41d4-a716-446655440000")
        assert result == SegmentType.UUID

    def test_int_before_hash(self):
        """Pure digits should match INT before HASH."""
        # 32-digit number could be hash, but INT takes priority
        assert classify_segment("12345678901234567890123456789012") == SegmentType.INT

    def test_32_digit_number_returns_int(self):
        """32-digit pure number should return INT, not HASH."""
        assert classify_segment("99999999999999999999999999999999") == SegmentType.INT

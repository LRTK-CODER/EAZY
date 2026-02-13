"""Unit tests for URL pattern classification and normalization."""

from eazy.crawler.url_pattern import URLPatternNormalizer, classify_segment
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


class TestNormalizeUrl:
    """Tests for URLPatternNormalizer.normalize_url_to_pattern."""

    def setup_method(self):
        self.normalizer = URLPatternNormalizer()

    def test_normalize_url_single_int_segment(self):
        """/posts/123 → /posts/<int>."""
        pat = self.normalizer.normalize_url_to_pattern("https://example.com/posts/123")
        assert pat.pattern_path == "/posts/<int>"
        assert pat.segment_types == (SegmentType.INT,)

    def test_normalize_url_uuid_segment(self):
        """/items/550e8400-... → /items/<uuid>."""
        pat = self.normalizer.normalize_url_to_pattern(
            "https://example.com/items/550e8400-e29b-41d4-a716-446655440000"
        )
        assert pat.pattern_path == "/items/<uuid>"
        assert pat.segment_types == (SegmentType.UUID,)

    def test_normalize_url_multiple_dynamic_segments(self):
        """/users/123/posts/456 → /users/<int>/posts/<int>."""
        pat = self.normalizer.normalize_url_to_pattern(
            "https://example.com/users/123/posts/456"
        )
        assert pat.pattern_path == "/users/<int>/posts/<int>"
        assert pat.segment_types == (
            SegmentType.INT,
            SegmentType.INT,
        )

    def test_normalize_url_no_dynamic_segments(self):
        """/about → /about (no dynamic segments)."""
        pat = self.normalizer.normalize_url_to_pattern("https://example.com/about")
        assert pat.pattern_path == "/about"
        assert pat.segment_types == ()

    def test_normalize_url_mixed_literal_and_dynamic(self):
        """/api/v2/users/123 → /api/v2/users/<int>."""
        pat = self.normalizer.normalize_url_to_pattern(
            "https://example.com/api/v2/users/123"
        )
        assert pat.pattern_path == "/api/v2/users/<int>"
        assert pat.segment_types == (SegmentType.INT,)

    def test_normalize_url_root_path(self):
        """/ → / (root path)."""
        pat = self.normalizer.normalize_url_to_pattern("https://example.com/")
        assert pat.pattern_path == "/"
        assert pat.segment_types == ()

    def test_normalize_url_preserves_scheme_and_host(self):
        """Scheme and netloc are preserved in the pattern."""
        pat = self.normalizer.normalize_url_to_pattern(
            "http://api.example.com:8080/users/42"
        )
        assert pat.scheme == "http"
        assert pat.netloc == "api.example.com:8080"

    def test_normalize_url_date_segment(self):
        """/archive/2025-01-15 → /archive/<date>."""
        pat = self.normalizer.normalize_url_to_pattern(
            "https://example.com/archive/2025-01-15"
        )
        assert pat.pattern_path == "/archive/<date>"
        assert pat.segment_types == (SegmentType.DATE,)

    def test_normalize_url_hash_segment(self):
        """40-char hex → /commit/<hash>."""
        pat = self.normalizer.normalize_url_to_pattern(
            "https://example.com/commit/da39a3ee5e6b4b0d3255bfef95601890afd80709"
        )
        assert pat.pattern_path == "/commit/<hash>"
        assert pat.segment_types == (SegmentType.HASH,)

    def test_normalize_url_slug_segment(self):
        """/blog/my-first-post → /blog/<slug>."""
        pat = self.normalizer.normalize_url_to_pattern(
            "https://example.com/blog/my-first-post"
        )
        assert pat.pattern_path == "/blog/<slug>"
        assert pat.segment_types == (SegmentType.SLUG,)


class TestGroupingAndSampling:
    """Tests for URLPatternNormalizer grouping, sampling, and promotion."""

    def setup_method(self):
        self.normalizer = URLPatternNormalizer(max_samples=3)

    def test_add_url_first_url_returns_true(self):
        """First URL for a new pattern should return True."""
        assert self.normalizer.add_url("https://example.com/posts/1") is True

    def test_add_url_same_pattern_within_limit_returns_true(self):
        """URLs within sample limit should return True."""
        self.normalizer.add_url("https://example.com/posts/1")
        self.normalizer.add_url("https://example.com/posts/2")
        assert self.normalizer.add_url("https://example.com/posts/3") is True

    def test_add_url_same_pattern_exceeds_limit_returns_false(self):
        """URLs beyond sample limit should return False."""
        self.normalizer.add_url("https://example.com/posts/1")
        self.normalizer.add_url("https://example.com/posts/2")
        self.normalizer.add_url("https://example.com/posts/3")
        assert self.normalizer.add_url("https://example.com/posts/4") is False

    def test_should_skip_unknown_pattern_returns_false(self):
        """Unknown pattern should not be skipped."""
        assert self.normalizer.should_skip("https://example.com/posts/1") is False

    def test_should_skip_full_pattern_returns_true(self):
        """Pattern at sample limit should be skipped."""
        for i in range(3):
            self.normalizer.add_url(f"https://example.com/posts/{i}")
        assert self.normalizer.should_skip("https://example.com/posts/999") is True

    def test_should_skip_partial_pattern_returns_false(self):
        """Pattern below sample limit should not be skipped."""
        self.normalizer.add_url("https://example.com/posts/1")
        assert self.normalizer.should_skip("https://example.com/posts/2") is False

    def test_type_promotion_mixed_int_and_slug_to_string(self):
        """Mixed INT and SLUG at same position promotes to STRING."""
        self.normalizer.add_url("https://example.com/items/123")
        self.normalizer.add_url("https://example.com/items/my-item")
        result = self.normalizer.get_results()
        group = result.groups[0]
        assert group.pattern.pattern_path == "/items/<string>"
        assert group.pattern.segment_types == (SegmentType.STRING,)

    def test_type_promotion_same_types_preserved(self):
        """Same types at same position are not promoted."""
        self.normalizer.add_url("https://example.com/posts/1")
        self.normalizer.add_url("https://example.com/posts/2")
        result = self.normalizer.get_results()
        group = result.groups[0]
        assert group.pattern.pattern_path == "/posts/<int>"
        assert group.pattern.segment_types == (SegmentType.INT,)

    def test_type_promotion_updates_existing_group(self):
        """Type promotion updates the group pattern correctly."""
        self.normalizer.add_url("https://example.com/users/123/posts/456")
        self.normalizer.add_url("https://example.com/users/admin-user/posts/789")
        result = self.normalizer.get_results()
        group = result.groups[0]
        assert group.pattern.pattern_path == "/users/<string>/posts/<int>"

    def test_get_results_correct_statistics(self):
        """get_results returns correct statistics."""
        for i in range(5):
            self.normalizer.add_url(f"https://example.com/posts/{i}")
        result = self.normalizer.get_results()
        assert result.total_urls_processed == 5
        assert result.total_patterns_found == 1
        assert result.total_urls_skipped == 2

    def test_get_results_multiple_groups(self):
        """Different structures produce separate groups."""
        self.normalizer.add_url("https://example.com/posts/1")
        self.normalizer.add_url("https://example.com/users/42/profile")
        result = self.normalizer.get_results()
        assert result.total_patterns_found == 2
        assert len(result.groups) == 2

    def test_custom_max_samples_value(self):
        """Custom max_samples is respected."""
        normalizer = URLPatternNormalizer(max_samples=5)
        for i in range(6):
            normalizer.add_url(f"https://example.com/posts/{i}")
        result = normalizer.get_results()
        group = result.groups[0]
        assert len(group.sample_urls) == 5
        assert group.total_count == 6

    def test_add_url_literal_only_paths_each_separate_group(self):
        """Literal-only paths with different names are separate."""
        self.normalizer.add_url("https://example.com/about")
        self.normalizer.add_url("https://example.com/contact")
        result = self.normalizer.get_results()
        assert result.total_patterns_found == 2

    def test_add_url_query_params_ignored_in_pattern(self):
        """Query parameters should not affect the pattern."""
        self.normalizer.add_url("https://example.com/posts/1?page=2")
        self.normalizer.add_url("https://example.com/posts/2?sort=asc")
        result = self.normalizer.get_results()
        assert result.total_patterns_found == 1
        group = result.groups[0]
        assert group.pattern.pattern_path == "/posts/<int>"

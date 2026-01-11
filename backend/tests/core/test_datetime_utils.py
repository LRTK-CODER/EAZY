"""Tests for datetime utilities.

TDD Step 1: RED - Tests written before implementation.
These tests verify utc_now() and utc_now_tz() functions.
"""

from datetime import datetime, timezone, timedelta


class TestUtcNow:
    """Tests for utc_now() function - offset-naive datetime."""

    def test_utc_now_returns_datetime(self):
        """utc_now() should return a datetime object."""
        from app.core.utils import utc_now

        result = utc_now()
        assert isinstance(result, datetime)

    def test_utc_now_is_offset_naive(self):
        """utc_now() should return offset-naive datetime (no tzinfo)."""
        from app.core.utils import utc_now

        result = utc_now()
        assert result.tzinfo is None

    def test_utc_now_represents_utc_time(self):
        """utc_now() should return time close to current UTC time."""
        from app.core.utils import utc_now

        result = utc_now()
        # Compare with UTC time (remove tzinfo for comparison)
        utc_reference = datetime.now(timezone.utc).replace(tzinfo=None)

        # Should be within 1 second of each other
        diff = abs((result - utc_reference).total_seconds())
        assert diff < 1.0

    def test_utc_now_has_no_tzinfo(self):
        """utc_now() tzinfo attribute should be None."""
        from app.core.utils import utc_now

        result = utc_now()
        assert result.tzinfo is None


class TestUtcNowTz:
    """Tests for utc_now_tz() function - timezone-aware datetime."""

    def test_utc_now_tz_returns_datetime(self):
        """utc_now_tz() should return a datetime object."""
        from app.core.utils import utc_now_tz

        result = utc_now_tz()
        assert isinstance(result, datetime)

    def test_utc_now_tz_is_timezone_aware(self):
        """utc_now_tz() should return timezone-aware datetime."""
        from app.core.utils import utc_now_tz

        result = utc_now_tz()
        assert result.tzinfo is not None

    def test_utc_now_tz_has_utc_tzinfo(self):
        """utc_now_tz() should have UTC timezone."""
        from app.core.utils import utc_now_tz

        result = utc_now_tz()
        assert result.tzinfo == timezone.utc

    def test_utc_now_tz_isoformat_includes_offset(self):
        """utc_now_tz().isoformat() should include timezone offset."""
        from app.core.utils import utc_now_tz

        result = utc_now_tz()
        iso_str = result.isoformat()

        # Should end with +00:00 for UTC
        assert "+00:00" in iso_str or "Z" in iso_str


class TestDatetimeArithmetic:
    """Tests for datetime arithmetic operations."""

    def test_utc_now_arithmetic_with_timedelta(self):
        """utc_now() should support timedelta arithmetic."""
        from app.core.utils import utc_now

        now = utc_now()
        future = now + timedelta(hours=1)
        past = now - timedelta(hours=1)

        assert future > now
        assert past < now
        assert (future - now).total_seconds() == 3600
        assert (now - past).total_seconds() == 3600

    def test_utc_now_tz_arithmetic_with_timedelta(self):
        """utc_now_tz() should support timedelta arithmetic."""
        from app.core.utils import utc_now_tz

        now = utc_now_tz()
        future = now + timedelta(hours=1)
        past = now - timedelta(hours=1)

        assert future > now
        assert past < now
        assert (future - now).total_seconds() == 3600
        assert (now - past).total_seconds() == 3600

    def test_utc_now_tz_fromisoformat_compatible(self):
        """utc_now_tz() should be compatible with fromisoformat() for arithmetic.

        This is critical for recovery.py where we parse ISO strings from Redis.
        """
        from app.core.utils import utc_now_tz

        # Simulate storing to Redis
        now = utc_now_tz()
        iso_string = now.isoformat()

        # Simulate reading from Redis
        parsed = datetime.fromisoformat(iso_string)

        # Should be able to do arithmetic without TypeError
        elapsed = (utc_now_tz() - parsed).total_seconds()
        assert isinstance(elapsed, float)
        assert elapsed >= 0  # Should be non-negative (time has passed)


class TestBackwardsCompatibility:
    """Tests for backwards compatibility with legacy implementations."""

    def test_utc_now_matches_legacy_implementation(self):
        """utc_now() should produce same result as legacy implementation."""
        from app.core.utils import utc_now

        # Legacy implementation from models
        legacy_result = datetime.now(timezone.utc).replace(tzinfo=None)
        new_result = utc_now()

        # Both should be offset-naive
        assert legacy_result.tzinfo is None
        assert new_result.tzinfo is None

        # Should be very close in time (within 1 second)
        diff = abs((new_result - legacy_result).total_seconds())
        assert diff < 1.0

"""
Test 5-Imp.32: URL Parameter Parsing Tests (RED Phase)
Expected to FAIL: ImportError - parse_query_params function doesn't exist yet
"""
import pytest


def test_parse_query_params_function_exists():
    """Test parse_query_params(url) function exists - RED Phase"""
    # Should FAIL: ImportError - cannot import name 'parse_query_params'
    from app.utils.url_parser import parse_query_params

    assert callable(parse_query_params), "parse_query_params should be a callable function"


def test_parse_query_params_extracts_parameters():
    """Test query parameter extraction returns dict {key: value} - RED Phase"""
    # Should FAIL: ImportError
    from app.utils.url_parser import parse_query_params

    url = "http://example.com/search?q=test&page=1&category=books"
    result = parse_query_params(url)

    assert isinstance(result, dict), "Should return a dictionary"
    assert result["q"] == "test", "Should extract 'q' parameter"
    assert result["page"] == "1", "Should extract 'page' parameter"
    assert result["category"] == "books", "Should extract 'category' parameter"


def test_parse_query_params_handles_multiple_values():
    """Test multiple values handling: key=val1&key=val2 → [val1, val2] - RED Phase"""
    # Should FAIL: ImportError
    from app.utils.url_parser import parse_query_params

    url = "http://example.com/filter?tag=python&tag=django&tag=web"
    result = parse_query_params(url)

    assert isinstance(result, dict), "Should return a dictionary"
    assert "tag" in result, "Should have 'tag' key"

    # Multiple values should be in a list
    tags = result["tag"]
    assert isinstance(tags, list), "Multiple values should be in a list"
    assert len(tags) == 3, "Should have 3 values"
    assert "python" in tags
    assert "django" in tags
    assert "web" in tags


def test_parse_query_params_url_decoding():
    """Test URL decoding (%20 → space) - RED Phase"""
    # Should FAIL: ImportError
    from app.utils.url_parser import parse_query_params

    # URL with encoded characters
    url = "http://example.com/search?q=hello%20world&name=John%20Doe"
    result = parse_query_params(url)

    assert isinstance(result, dict), "Should return a dictionary"
    assert result["q"] == "hello world", "Should decode %20 to space"
    assert result["name"] == "John Doe", "Should decode %20 to space"


def test_parse_query_params_empty_query():
    """Test empty dict returned for URL without query - RED Phase"""
    # Should FAIL: ImportError
    from app.utils.url_parser import parse_query_params

    # URL without query string
    url1 = "http://example.com/about"
    result1 = parse_query_params(url1)
    assert result1 == {}, "Should return empty dict for URL without query"

    # URL with only fragment (no query)
    url2 = "http://example.com/page#section"
    result2 = parse_query_params(url2)
    assert result2 == {}, "Should return empty dict when no query parameters"

    # URL with empty query
    url3 = "http://example.com/page?"
    result3 = parse_query_params(url3)
    assert result3 == {}, "Should return empty dict for empty query string"

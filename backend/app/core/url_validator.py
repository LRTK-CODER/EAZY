"""
URL Validation utilities for SSRF prevention.

This module provides URL safety validation to prevent Server-Side Request Forgery (SSRF)
attacks. It should be used both at task creation (fast-fail) and during crawl execution
(defense-in-depth).

Usage:
    from app.core.url_validator import is_safe_url, validate_url
    from app.core.exceptions import UnsafeUrlError

    # Check and get boolean
    if not is_safe_url(url):
        # handle unsafe URL

    # Or raise exception directly
    validate_url(url)  # raises UnsafeUrlError if unsafe
"""

import ipaddress
from typing import Optional
from urllib.parse import urlparse

from app.core.exceptions import UnsafeUrlError


# SSRF Prevention - Blocked schemes and hosts
BLOCKED_SCHEMES: frozenset[str] = frozenset({"file", "gopher", "ftp", "data"})
BLOCKED_HOSTS: frozenset[str] = frozenset({"localhost", "127.0.0.1", "::1", "[::1]"})


def is_safe_url(url: Optional[str]) -> bool:
    """
    Validate URL for SSRF prevention.

    Blocks:
    - Internal/private IP addresses (10.x, 172.16-31.x, 192.168.x)
    - Loopback addresses (localhost, 127.0.0.1, ::1)
    - AWS metadata endpoint (169.254.169.254)
    - Dangerous schemes (file://, gopher://, ftp://)

    Args:
        url: URL to validate

    Returns:
        True if URL is safe to crawl, False otherwise
    """
    if not url:
        return False

    try:
        parsed = urlparse(url)

        # Must have a scheme
        if not parsed.scheme:
            return False

        # Block dangerous schemes
        if parsed.scheme.lower() in BLOCKED_SCHEMES:
            return False

        # Must have a hostname
        hostname = parsed.hostname
        if not hostname:
            return False

        # Block known dangerous hosts
        if hostname.lower() in BLOCKED_HOSTS:
            return False

        # Check if hostname is an IP address
        try:
            ip = ipaddress.ip_address(hostname)
            # Block private, reserved, loopback IPs
            if ip.is_private or ip.is_reserved or ip.is_loopback:
                return False
            # Block link-local addresses (169.254.x.x - AWS metadata)
            if ip.is_link_local:
                return False
        except ValueError:
            # hostname is a domain name, not an IP - that's fine
            pass

        return True
    except Exception:
        return False


def get_unsafe_reason(url: Optional[str]) -> Optional[str]:
    """
    Get the reason why a URL is considered unsafe.

    Args:
        url: URL to validate

    Returns:
        Reason string if unsafe, None if safe
    """
    if not url:
        return "empty_url"

    try:
        parsed = urlparse(url)

        if not parsed.scheme:
            return "missing_scheme"

        if parsed.scheme.lower() in BLOCKED_SCHEMES:
            return f"blocked_scheme_{parsed.scheme}"

        hostname = parsed.hostname
        if not hostname:
            return "missing_hostname"

        if hostname.lower() in BLOCKED_HOSTS:
            return "loopback_address"

        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private:
                return "private_ip"
            if ip.is_reserved:
                return "reserved_ip"
            if ip.is_loopback:
                return "loopback_ip"
            if ip.is_link_local:
                return "link_local_ip"
        except ValueError:
            pass

        return None
    except Exception:
        return "parse_error"


def validate_url(url: Optional[str]) -> None:
    """
    Validate URL and raise UnsafeUrlError if not safe.

    Args:
        url: URL to validate

    Raises:
        UnsafeUrlError: If URL is not safe to crawl
    """
    reason = get_unsafe_reason(url)
    if reason:
        raise UnsafeUrlError(url=url or "", reason=reason)

"""URL validation service for SSRF prevention."""

import ipaddress
import socket
from dataclasses import dataclass
from typing import Optional, Set
from urllib.parse import urlparse


@dataclass(frozen=True)
class ValidationResult:
    """URL 검증 결과"""

    is_safe: bool
    reason: str = ""


class UrlValidator:
    """SSRF 방지를 위한 URL 검증기"""

    BLOCKED_SCHEMES: Set[str] = {"file", "gopher", "ftp", "data"}
    BLOCKED_HOSTS: Set[str] = {"localhost", "127.0.0.1", "::1", "[::1]"}

    def is_safe(self, url: Optional[str]) -> bool:
        """URL이 안전한지 검증 (boolean 반환)"""
        return self.validate(url).is_safe

    def validate(self, url: Optional[str]) -> ValidationResult:
        """
        URL 검증 + 이유 반환

        Blocks:
        - Internal/private IP addresses (10.x, 172.16-31.x, 192.168.x)
        - Loopback addresses (localhost, 127.0.0.1, ::1)
        - AWS metadata endpoint (169.254.169.254)
        - Dangerous schemes (file://, gopher://, ftp://)

        Args:
            url: URL to validate

        Returns:
            ValidationResult with is_safe flag and reason
        """
        if not url:
            return ValidationResult(is_safe=False, reason="URL is empty or None")

        try:
            parsed = urlparse(url)

            # Must have a scheme
            if not parsed.scheme:
                return ValidationResult(is_safe=False, reason="URL missing scheme")

            # Block dangerous schemes
            if parsed.scheme.lower() in self.BLOCKED_SCHEMES:
                return ValidationResult(
                    is_safe=False,
                    reason=f"Blocked scheme: {parsed.scheme}",
                )

            # Must have a hostname
            hostname = parsed.hostname
            if not hostname:
                return ValidationResult(is_safe=False, reason="URL missing hostname")

            # Block known dangerous hosts
            if hostname.lower() in self.BLOCKED_HOSTS:
                return ValidationResult(
                    is_safe=False,
                    reason=f"Blocked loopback/localhost: {hostname}",
                )

            # Check if hostname is an IP address
            try:
                ip = ipaddress.ip_address(hostname)
                # Block private, reserved, loopback IPs
                if ip.is_private:
                    return ValidationResult(
                        is_safe=False,
                        reason=f"Blocked private IP: {hostname}",
                    )
                if ip.is_reserved:
                    return ValidationResult(
                        is_safe=False,
                        reason=f"Blocked reserved IP: {hostname}",
                    )
                if ip.is_loopback:
                    return ValidationResult(
                        is_safe=False,
                        reason=f"Blocked loopback IP: {hostname}",
                    )
                # Block link-local addresses (169.254.x.x - AWS metadata)
                if ip.is_link_local:
                    return ValidationResult(
                        is_safe=False,
                        reason=f"Blocked link-local IP: {hostname}",
                    )
            except ValueError:
                # hostname is a domain name - resolve and check IPs
                try:
                    # Resolve domain to check actual IPs
                    resolved_ips = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC)
                    for family, _, _, _, sockaddr in resolved_ips:
                        ip_str = sockaddr[0]
                        try:
                            ip = ipaddress.ip_address(ip_str)
                            if ip.is_private:
                                return ValidationResult(
                                    is_safe=False,
                                    reason=f"Domain {hostname} resolves to private IP: {ip_str}",
                                )
                            if ip.is_reserved:
                                return ValidationResult(
                                    is_safe=False,
                                    reason=f"Domain {hostname} resolves to reserved IP: {ip_str}",
                                )
                            if ip.is_loopback:
                                return ValidationResult(
                                    is_safe=False,
                                    reason=f"Domain {hostname} resolves to loopback IP: {ip_str}",
                                )
                            if ip.is_link_local:
                                return ValidationResult(
                                    is_safe=False,
                                    reason=f"Domain {hostname} resolves to link-local IP: {ip_str}",
                                )
                        except ValueError:
                            # Not a valid IP (shouldn't happen but be safe)
                            continue
                except socket.gaierror:
                    # DNS resolution failed - allow the request (could be internal DNS issue)
                    # Or optionally: block if strict mode is needed
                    pass

            return ValidationResult(is_safe=True, reason="URL is safe")
        except Exception as e:
            return ValidationResult(
                is_safe=False,
                reason=f"URL parsing error: {str(e)}",
            )

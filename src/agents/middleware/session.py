"""Session middleware — cookie/JWT/CSRF management and scope boundary."""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime
from fnmatch import fnmatch
from http.cookies import SimpleCookie
from urllib.parse import urlparse

import httpx


class CookieManager:
    """Manages HTTP cookies: extract from responses, inject into requests."""

    def __init__(self) -> None:
        self._cookies: dict[str, tuple[str, datetime | None]] = {}

    def extract_cookies(self, response: httpx.Response) -> None:
        """Extract Set-Cookie headers from a response and store them."""
        raw_headers = response.headers.multi_items()
        for name, value in raw_headers:
            if name.lower() != "set-cookie":
                continue
            self._parse_set_cookie(value)

    def _parse_set_cookie(self, raw: str) -> None:
        """Parse a single Set-Cookie header value."""
        sc: SimpleCookie = SimpleCookie()
        sc.load(raw)
        for key, morsel in sc.items():
            expires: datetime | None = None
            max_age = morsel.get("max-age", "")
            if max_age and max_age != "0":
                expires = datetime.now(UTC).replace(
                    microsecond=0,
                ) + __import__("datetime").timedelta(seconds=int(max_age))
            elif max_age == "0":
                expires = datetime(2000, 1, 1, tzinfo=UTC)
            elif morsel.get("expires", ""):
                try:
                    from email.utils import parsedate_to_datetime

                    expires = parsedate_to_datetime(morsel["expires"]).replace(
                        tzinfo=UTC
                    )
                except (ValueError, TypeError):
                    pass
            self._cookies[key] = (morsel.value, expires)

    def get(self, name: str) -> str | None:
        """Get a cookie value by name, or None if missing/expired."""
        entry = self._cookies.get(name)
        if entry is None:
            return None
        value, expires = entry
        if expires is not None and expires <= datetime.now(UTC):
            return None
        return value

    def inject_cookies(self, request: httpx.Request) -> httpx.Request:
        """Inject non-expired cookies into the request Cookie header."""
        pairs: list[str] = []
        for name, (value, expires) in self._cookies.items():
            if expires is not None and expires <= datetime.now(UTC):
                continue
            pairs.append(f"{name}={value}")
        cookie_str = "; ".join(pairs)
        if cookie_str:
            request.headers["cookie"] = cookie_str
        return request

    def clear(self) -> None:
        """Remove all stored cookies."""
        self._cookies.clear()


class JWTManager:
    """Manages JWT access/refresh tokens."""

    def __init__(self) -> None:
        self._access_token: str | None = None
        self._refresh_token: str | None = None

    def set_tokens(
        self,
        access_token: str,
        refresh_token: str | None = None,
    ) -> None:
        """Store access and optional refresh tokens."""
        self._access_token = access_token
        self._refresh_token = refresh_token

    def is_expired(self) -> bool:
        """Check if the access token exp claim is in the past."""
        if self._access_token is None:
            return True
        payload = self._decode_payload(self._access_token)
        exp = payload.get("exp")
        if exp is None or not isinstance(exp, int | float):
            return False
        return datetime.now(UTC).timestamp() >= float(exp)

    def get_auth_header(self) -> dict[str, str]:
        """Return Authorization: Bearer header dict."""
        if self._access_token is None:
            return {}
        return {"Authorization": f"Bearer {self._access_token}"}

    async def refresh(
        self,
        client: httpx.AsyncClient,
        refresh_url: str,
    ) -> None:
        """Refresh the access token using the refresh token."""
        if self._refresh_token is None:
            msg = "No refresh token available"
            raise ValueError(msg)
        response = await client.post(
            refresh_url,
            json={"refresh_token": self._refresh_token},
        )
        data: dict[str, str] = response.json()
        new_access = data.get("access_token", "")
        new_refresh = data.get("refresh_token", self._refresh_token)
        self.set_tokens(access_token=new_access, refresh_token=new_refresh)

    @staticmethod
    def _decode_payload(token: str) -> dict[str, object]:
        """Decode the payload section of a JWT (no verification)."""
        parts = token.split(".")
        if len(parts) < 2:  # noqa: PLR2004
            return {}
        payload_b64 = parts[1]
        # Fix padding
        padding = 4 - len(payload_b64) % 4
        if padding != 4:  # noqa: PLR2004
            payload_b64 += "=" * padding
        raw = base64.urlsafe_b64decode(payload_b64)
        result: dict[str, object] = json.loads(raw)
        return result


class CSRFManager:
    """Manages CSRF token extraction and injection."""

    def __init__(
        self,
        token_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
    ) -> None:
        self.token_name = token_name
        self.header_name = header_name
        self.token: str | None = None

    def extract_token(self, response: httpx.Response) -> None:
        """Extract CSRF token from response header or JSON body."""
        # Priority 1: response header
        header_val = response.headers.get(self.header_name)
        if header_val:
            self.token = header_val
            return
        # Priority 2: JSON body
        try:
            body: dict[str, object] = response.json()
            token_val = body.get(self.token_name)
            if isinstance(token_val, str):
                self.token = token_val
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    def inject_token(self, request: httpx.Request) -> httpx.Request:
        """Inject stored CSRF token into request header."""
        if self.token is not None:
            request.headers[self.header_name] = self.token
        return request


class ScopeBoundary:
    """Enforces target scope boundaries for HTTP requests."""

    def __init__(
        self,
        scope: list[str],
        exclude: list[str] | None = None,
    ) -> None:
        self._scope = scope
        self._exclude = exclude or []

    def is_in_scope(self, url: str) -> bool:
        """Check if a URL's hostname is within the allowed scope."""
        hostname = urlparse(url).hostname or ""
        # Check exclude list first
        for pattern in self._exclude:
            if fnmatch(hostname, pattern):
                return False
        # Check scope
        return any(fnmatch(hostname, pattern) for pattern in self._scope)


class SessionMiddleware:
    """Composition of cookie/JWT/CSRF managers with scope enforcement.

    Wraps an httpx.AsyncClient to automatically manage session state.
    """

    def __init__(
        self,
        client: httpx.AsyncClient,
        scope: list[str],
        exclude: list[str] | None = None,
        csrf_token_name: str = "csrf_token",
        csrf_header_name: str = "X-CSRF-Token",
    ) -> None:
        self._client = client
        self.cookies = CookieManager()
        self.jwt = JWTManager()
        self.csrf = CSRFManager(
            token_name=csrf_token_name,
            header_name=csrf_header_name,
        )
        self.scope = ScopeBoundary(scope=scope, exclude=exclude)

    async def send(self, request: httpx.Request) -> httpx.Response:
        """Send a request with full session middleware pipeline."""
        url_str = str(request.url)
        if not self.scope.is_in_scope(url_str):
            msg = f"URL out of scope: {url_str}"
            raise ValueError(msg)
        # Inject cookies, JWT, CSRF
        self.cookies.inject_cookies(request)
        auth_header = self.jwt.get_auth_header()
        for key, value in auth_header.items():
            request.headers[key] = value
        self.csrf.inject_token(request)
        # Send
        response = await self._client.send(request)
        # Extract from response
        self.cookies.extract_cookies(response)
        self.csrf.extract_token(response)
        return response

    async def request(
        self,
        method: str,
        url: str,
        **kwargs: object,
    ) -> httpx.Response:
        """Build an httpx.Request and send through the middleware pipeline."""
        req = httpx.Request(method, url, **kwargs)  # type: ignore[arg-type]
        return await self.send(req)

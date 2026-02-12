"""Robots.txt parser for crawl permission checking."""

from __future__ import annotations

import re
from urllib.parse import urlparse


class RobotsParser:
    """Parse robots.txt content and check URL permissions.

    Attributes:
        _rules: Mapping of lowercase user-agent to list of (is_allow, pattern) tuples.
        _crawl_delays: Mapping of lowercase user-agent to delay in seconds.
    """

    def __init__(self, robots_txt: str) -> None:
        """Parse robots.txt content into structured rules.

        Args:
            robots_txt: Raw robots.txt file content.
        """
        self._rules: dict[str, list[tuple[bool, str]]] = {}
        self._crawl_delays: dict[str, float] = {}

        current_agents: list[str] = []

        for raw_line in robots_txt.splitlines():
            # Strip comments and whitespace
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue

            # Split directive and value
            if ":" not in line:
                continue
            directive, _, value = line.partition(":")
            directive = directive.strip().lower()
            value = value.strip()

            if directive == "user-agent":
                agent = value.lower()
                # A new user-agent after rules resets the agent list
                if current_agents and current_agents[-1] in self._rules:
                    current_agents = []
                current_agents.append(agent)
                if agent not in self._rules:
                    self._rules[agent] = []
            elif directive == "disallow" and current_agents:
                if value:
                    for agent in current_agents:
                        self._rules[agent].append((False, value))
            elif directive == "allow" and current_agents:
                if value:
                    for agent in current_agents:
                        self._rules[agent].append((True, value))
            elif directive == "crawl-delay" and current_agents:
                try:
                    delay = float(value)
                    for agent in current_agents:
                        self._crawl_delays[agent] = delay
                except ValueError:
                    pass

    def get_crawl_delay(self, user_agent: str = "*") -> float | None:
        """Get the crawl delay for a user agent.

        Args:
            user_agent: User-agent string to look up.

        Returns:
            Delay in seconds, or None if not specified.
        """
        agent = user_agent.lower()
        if agent in self._crawl_delays:
            return self._crawl_delays[agent]
        return None

    def is_allowed(self, url: str, user_agent: str = "*") -> bool:
        """Check whether a URL is allowed for the given user agent.

        Args:
            url: Absolute URL to check.
            user_agent: User-agent string. Defaults to "*".

        Returns:
            True if crawling is allowed, False otherwise.
        """
        path = urlparse(url).path

        agent = user_agent.lower()

        # Use specific UA rules if available, otherwise fall back to *
        if agent in self._rules:
            rules = self._rules[agent]
        elif "*" in self._rules:
            rules = self._rules["*"]
        else:
            return True

        # Find the most specific matching rule (longest pattern wins).
        # If tied on length, Allow wins over Disallow.
        best_match: tuple[bool, str] | None = None
        best_length = -1

        for is_allow, pattern in rules:
            if self._match_pattern(path, pattern):
                pat_len = len(pattern)
                if pat_len > best_length or (pat_len == best_length and is_allow):
                    best_match = (is_allow, pattern)
                    best_length = pat_len

        if best_match is None:
            return True

        return best_match[0]

    @staticmethod
    def _match_pattern(path: str, pattern: str) -> bool:
        """Match a URL path against a robots.txt pattern.

        Supports ``*`` wildcard and ``$`` end-of-string anchor.

        Args:
            path: URL path to test.
            pattern: Robots.txt pattern (e.g. ``/admin``, ``/*.pdf``).

        Returns:
            True if the path matches the pattern.
        """
        # Convert robots.txt pattern to regex:
        #   * → .* (wildcard), $ → $ (end anchor), others → escaped
        parts = []
        for char in pattern:
            if char == "*":
                parts.append(".*")
            elif char == "$":
                parts.append("$")
            else:
                parts.append(re.escape(char))

        regex = f"^{''.join(parts)}"
        return re.search(regex, path) is not None

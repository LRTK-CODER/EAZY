"""Unit tests for robots.txt parser module."""

from eazy.crawler.robots_parser import RobotsParser


class TestRobotsParser:
    def test_parse_basic_user_agent_disallow(self):
        # Arrange
        robots_txt = "User-agent: *\nDisallow: /admin"

        # Act
        parser = RobotsParser(robots_txt)

        # Assert
        assert parser._rules["*"] == [(False, "/admin")]

    def test_parse_empty_robots_txt(self):
        # Arrange
        robots_txt = ""

        # Act
        parser = RobotsParser(robots_txt)

        # Assert
        assert parser._rules == {}

    def test_parse_ignores_comments(self):
        # Arrange
        robots_txt = (
            "# This is a comment\n"
            "User-agent: *\n"
            "# Another comment\n"
            "Disallow: /private\n"
        )

        # Act
        parser = RobotsParser(robots_txt)

        # Assert
        assert parser._rules["*"] == [(False, "/private")]

    def test_parse_multiple_user_agent_blocks(self):
        # Arrange
        robots_txt = (
            "User-agent: Googlebot\n"
            "Disallow: /nogoogle\n"
            "\n"
            "User-agent: *\n"
            "Disallow: /secret\n"
        )

        # Act
        parser = RobotsParser(robots_txt)

        # Assert
        assert parser._rules["googlebot"] == [(False, "/nogoogle")]
        assert parser._rules["*"] == [(False, "/secret")]

    def test_parse_allow_and_disallow(self):
        # Arrange
        robots_txt = "User-agent: *\nAllow: /public\nDisallow: /\n"

        # Act
        parser = RobotsParser(robots_txt)

        # Assert
        assert (True, "/public") in parser._rules["*"]
        assert (False, "/") in parser._rules["*"]

    def test_parse_crawl_delay(self):
        # Arrange
        robots_txt = "User-agent: *\nCrawl-delay: 2.5\nDisallow: /admin\n"

        # Act
        parser = RobotsParser(robots_txt)

        # Assert
        assert parser.get_crawl_delay("*") == 2.5

    def test_get_crawl_delay_returns_none_when_not_set(self):
        # Arrange
        robots_txt = "User-agent: *\nDisallow: /admin"

        # Act
        parser = RobotsParser(robots_txt)

        # Assert
        assert parser.get_crawl_delay("*") is None

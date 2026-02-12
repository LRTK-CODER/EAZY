"""Unit tests for HTML regex parser."""


from eazy.crawler.regex_parser import extract_buttons, extract_forms, extract_links
from eazy.models.crawl_types import ButtonInfo, FormData


class TestExtractLinks:
    def test_extract_links_from_basic_anchor_tag(self):
        # Arrange
        html = '<a href="/page">Link</a>'

        # Act
        result = extract_links(html)

        # Assert
        assert result == ["/page"]

    def test_extract_links_from_multiple_anchors(self):
        # Arrange
        html = """
            <a href="/page1">Link 1</a>
            <a href="https://example.com/page2">Link 2</a>
            <a href="/page3">Link 3</a>
        """

        # Act
        result = extract_links(html)

        # Assert
        assert result == ["/page1", "https://example.com/page2", "/page3"]

    def test_extract_links_from_empty_html_returns_empty_list(self):
        # Arrange
        html = ""

        # Act
        result = extract_links(html)

        # Assert
        assert result == []

    def test_extract_links_ignores_anchor_without_href(self):
        # Arrange
        html = '<a name="top">No Link</a>'

        # Act
        result = extract_links(html)

        # Assert
        assert result == []

    def test_extract_links_handles_both_quote_styles(self):
        # Arrange
        html = """
            <a href="/double-quotes">Link 1</a>
            <a href='/single-quotes'>Link 2</a>
        """

        # Act
        result = extract_links(html)

        # Assert
        assert result == ["/double-quotes", "/single-quotes"]

    def test_extract_links_ignores_javascript_mailto_tel_protocols(self):
        # Arrange
        html = """
            <a href="javascript:void(0)">JS Link</a>
            <a href="mailto:a@b.com">Email</a>
            <a href="tel:123">Phone</a>
            <a href="/valid">Valid Link</a>
        """

        # Act
        result = extract_links(html)

        # Assert
        assert result == ["/valid"]


class TestExtractForms:
    def test_extract_forms_basic_form(self):
        # Arrange
        html = (
            '<form action="/login" method="POST">'
            '<input name="user" type="text"></form>'
        )

        # Act
        result = extract_forms(html)

        # Assert
        assert len(result) == 1
        assert result[0].action == "/login"
        assert result[0].method == "POST"

    def test_extract_forms_extracts_input_fields(self):
        # Arrange
        html = """
            <form action="/submit" method="POST">
                <input name="username" type="text" value="">
                <input name="password" type="password" value="">
                <input name="remember" type="checkbox" value="1">
            </form>
        """

        # Act
        result = extract_forms(html)

        # Assert
        assert len(result) == 1
        assert len(result[0].inputs) == 3
        assert all(isinstance(inp, dict) for inp in result[0].inputs)
        assert all(
            "name" in inp and "type" in inp and "value" in inp
            for inp in result[0].inputs
        )

    def test_extract_forms_multiple_forms(self):
        # Arrange
        html = """
            <form action="/login" method="POST">
                <input name="user" type="text">
            </form>
            <form action="/search" method="GET">
                <input name="q" type="text">
            </form>
        """

        # Act
        result = extract_forms(html)

        # Assert
        assert len(result) == 2
        assert result[0].action == "/login"
        assert result[1].action == "/search"

    def test_extract_forms_without_action(self):
        # Arrange
        html = '<form><input name="q"></form>'

        # Act
        result = extract_forms(html)

        # Assert
        assert len(result) == 1
        assert result[0].action == ""

    def test_extract_forms_default_method_get(self):
        # Arrange
        html = '<form action="/search"><input name="q"></form>'

        # Act
        result = extract_forms(html)

        # Assert
        assert len(result) == 1
        assert result[0].method == "GET"

    def test_extract_forms_select_and_textarea(self):
        # Arrange
        html = """
            <form action="/profile" method="POST">
                <select name="color">
                    <option>Red</option>
                    <option>Blue</option>
                </select>
                <textarea name="bio"></textarea>
            </form>
        """

        # Act
        result = extract_forms(html)

        # Assert
        assert len(result) == 1
        assert len(result[0].inputs) == 2
        input_names = [inp["name"] for inp in result[0].inputs]
        input_types = [inp["type"] for inp in result[0].inputs]
        assert "color" in input_names
        assert "bio" in input_names
        assert "select" in input_types
        assert "textarea" in input_types

    def test_extract_forms_hidden_and_file_inputs(self):
        # Arrange
        html = """
            <form action="/upload" method="POST">
                <input type="hidden" name="token" value="abc">
                <input type="file" name="doc">
            </form>
        """

        # Act
        result = extract_forms(html)

        # Assert
        assert len(result) == 1
        assert result[0].has_file_upload is True
        input_names = [inp["name"] for inp in result[0].inputs]
        assert "token" in input_names
        assert "doc" in input_names


class TestExtractButtons:
    def test_extract_buttons_basic_button(self):
        # Arrange
        html = '<button>Click Me</button>'

        # Act
        result = extract_buttons(html)

        # Assert
        assert len(result) == 1
        assert result[0].text == "Click Me"
        assert result[0].type is None
        assert result[0].onclick is None

    def test_extract_buttons_with_onclick_handler(self):
        # Arrange
        html = '<button onclick="doSomething()">Act</button>'

        # Act
        result = extract_buttons(html)

        # Assert
        assert len(result) == 1
        assert result[0].text == "Act"
        assert result[0].onclick == "doSomething()"

    def test_extract_buttons_submit_type(self):
        # Arrange
        html = '<button type="submit">Submit</button>'

        # Act
        result = extract_buttons(html)

        # Assert
        assert len(result) == 1
        assert result[0].text == "Submit"
        assert result[0].type == "submit"

    def test_extract_buttons_from_empty_html_returns_empty_list(self):
        # Arrange
        html = ""

        # Act
        result = extract_buttons(html)

        # Assert
        assert result == []

    def test_extract_buttons_input_submit(self):
        # Arrange
        html = '<input type="submit" value="Go">'

        # Act
        result = extract_buttons(html)

        # Assert
        assert len(result) == 1
        assert result[0].text == "Go"
        assert result[0].type == "submit"
        assert result[0].onclick is None

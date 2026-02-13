"""Page analysis module for extracting links, forms, and metadata from pages.

This module provides PageAnalyzer class for analyzing rendered web pages using
Playwright to extract structured information including links, forms, buttons,
and SPA detection.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from eazy.crawler.url_resolver import resolve_url
from eazy.models.crawl_types import ButtonInfo, FormData, PageAnalysisResult

if TYPE_CHECKING:
    from playwright.async_api import Page

__all__ = ["PageAnalyzer"]

# Selector constants
_LINK_SELECTOR = "a[href]"
_FORM_SELECTOR = "form"
_FORM_INPUT_SELECTOR = "input, select, textarea"
_BUTTON_SELECTOR = "button, input[type='submit'], input[type='button']"
_SCRIPT_COUNT_JS = "() => document.querySelectorAll('script[src]').length"


class PageAnalyzer:
    """Analyze rendered web pages to extract links, forms, and metadata.

    Uses Playwright Page objects to query the DOM and extract structured
    information for smart crawling and attack surface mapping.
    """

    _SPA_MARKERS: ClassVar[list[str]] = [
        "#root",
        "#app",
        "#__next",
        "[data-reactroot]",
        "[ng-app]",
        "[data-v-]",
    ]
    _SKIP_HREF_PREFIXES: ClassVar[tuple[str, ...]] = (
        "javascript:",
        "mailto:",
        "tel:",
    )
    _SPA_SCRIPT_THRESHOLD: ClassVar[int] = 5

    def __init__(self, base_url: str) -> None:
        """Initialize PageAnalyzer with base URL for resolving relative URLs.

        Args:
            base_url: The base URL of the current page for URL resolution.
        """
        self._base_url = base_url

    async def extract_links(self, page: Page) -> list[str]:
        """Extract all valid links from the page.

        Args:
            page: Playwright Page object to analyze.

        Returns:
            Deduplicated list of absolute URLs found on the page.
            Fragment-only and protocol-specific links are filtered out.
        """
        try:
            elements = await page.query_selector_all(_LINK_SELECTOR)
            links = []
            seen = set()

            for el in elements:
                href = await el.get_attribute("href")
                if not href:
                    continue

                # Skip protocol-specific links
                if href.startswith(self._SKIP_HREF_PREFIXES):
                    continue

                # Resolve to absolute URL
                resolved = resolve_url(self._base_url, href)
                if resolved is None:
                    continue

                # Deduplicate while preserving order
                if resolved not in seen:
                    links.append(resolved)
                    seen.add(resolved)

            return links
        except Exception:
            return []

    async def extract_forms(self, page: Page) -> list[FormData]:
        """Extract all forms from the page with their fields.

        Args:
            page: Playwright Page object to analyze.

        Returns:
            List of FormData objects representing forms found on the page.
        """
        try:
            form_elements = await page.query_selector_all(_FORM_SELECTOR)
            forms = []

            for form in form_elements:
                # Get form action and method
                action_attr = await form.get_attribute("action")
                if action_attr:
                    action_url = resolve_url(self._base_url, action_attr)
                    if action_url is None:
                        action_url = self._base_url
                else:
                    action_url = self._base_url

                method_attr = await form.get_attribute("method")
                method = method_attr.upper() if method_attr else "GET"

                # Extract form fields
                input_elements = await form.query_selector_all(_FORM_INPUT_SELECTOR)
                inputs = []
                has_file_upload = False

                for input_el in input_elements:
                    name = await input_el.get_attribute("name")
                    input_type = await input_el.get_attribute("type")

                    inputs.append({"name": name, "type": input_type})

                    if input_type == "file":
                        has_file_upload = True

                forms.append(
                    FormData(
                        action=action_url,
                        method=method,
                        inputs=inputs,
                        has_file_upload=has_file_upload,
                    )
                )

            return forms
        except Exception:
            return []

    async def extract_buttons(self, page: Page) -> list[ButtonInfo]:
        """Extract all interactive buttons from the page.

        Args:
            page: Playwright Page object to analyze.

        Returns:
            List of ButtonInfo objects representing buttons on the page.
        """
        try:
            button_elements = await page.query_selector_all(_BUTTON_SELECTOR)
            buttons = []

            for el in button_elements:
                text = await el.text_content()
                text = text.strip() if text else ""

                button_type = await el.get_attribute("type")
                onclick = await el.get_attribute("onclick")

                buttons.append(ButtonInfo(text=text, type=button_type, onclick=onclick))

            return buttons
        except Exception:
            return []

    async def extract_title(self, page: Page) -> str | None:
        """Extract the page title.

        Args:
            page: Playwright Page object to analyze.

        Returns:
            The page title string, or None if empty.
        """
        try:
            title = await page.title()
            return title if title else None
        except Exception:
            return None

    async def detect_spa(self, page: Page) -> bool:
        """Detect if the page is a Single Page Application.

        Checks for common SPA framework markers and script count.

        Args:
            page: Playwright Page object to analyze.

        Returns:
            True if SPA characteristics detected, False otherwise.
        """
        try:
            # Check for SPA framework markers
            for marker in self._SPA_MARKERS:
                element = await page.query_selector(marker)
                if element is not None:
                    return True

            # Check script count threshold
            script_count = await page.evaluate(_SCRIPT_COUNT_JS)
            if script_count >= self._SPA_SCRIPT_THRESHOLD:
                return True

            return False
        except Exception:
            return False

    async def analyze(self, page: Page) -> PageAnalysisResult:
        """Perform complete page analysis.

        Extracts all information from the page including links, forms,
        buttons, title, and SPA detection.

        Args:
            page: Playwright Page object to analyze.

        Returns:
            PageAnalysisResult containing all extracted information.
        """
        links = await self.extract_links(page)
        forms = await self.extract_forms(page)
        buttons = await self.extract_buttons(page)
        title = await self.extract_title(page)
        is_spa = await self.detect_spa(page)

        return PageAnalysisResult(
            links=links,
            forms=forms,
            buttons=buttons,
            title=title,
            is_spa=is_spa,
        )

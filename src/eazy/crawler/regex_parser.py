"""Regex-based HTML parser for extracting page structure."""

from __future__ import annotations

import re

from eazy.models.crawl_types import ButtonInfo, FormData

# Compile regex pattern at module level for performance
HREF_PATTERN = re.compile(r'href\s*=\s*["\'](.*?)["\']', re.IGNORECASE)
FORM_PATTERN = re.compile(r'<form\b(.*?)>(.*?)</form>', re.DOTALL | re.IGNORECASE)
ACTION_PATTERN = re.compile(r'action\s*=\s*["\'](.*?)["\']', re.IGNORECASE)
METHOD_PATTERN = re.compile(r'method\s*=\s*["\'](.*?)["\']', re.IGNORECASE)
INPUT_PATTERN = re.compile(
    r'<input\b([^>]*?)/?>', re.DOTALL | re.IGNORECASE
)
SELECT_PATTERN = re.compile(
    r'<select\b([^>]*?)>.*?</select>', re.DOTALL | re.IGNORECASE
)
TEXTAREA_PATTERN = re.compile(
    r'<textarea\b([^>]*?)>.*?</textarea>', re.DOTALL | re.IGNORECASE
)
NAME_PATTERN = re.compile(r'name\s*=\s*["\'](.*?)["\']', re.IGNORECASE)
TYPE_PATTERN = re.compile(r'type\s*=\s*["\'](.*?)["\']', re.IGNORECASE)
VALUE_PATTERN = re.compile(r'value\s*=\s*["\'](.*?)["\']', re.IGNORECASE)
BUTTON_PATTERN = re.compile(
    r'<button\b([^>]*?)>(.*?)</button>', re.DOTALL | re.IGNORECASE
)
ONCLICK_PATTERN = re.compile(r'onclick\s*=\s*["\'](.*?)["\']', re.IGNORECASE)
INPUT_SUBMIT_PATTERN = re.compile(
    r'<input\b([^>]*?)type\s*=\s*["\'](?:submit|button)["\']([^>]*?)/?>',
    re.DOTALL | re.IGNORECASE
)

# Protocols to filter out
EXCLUDED_PROTOCOLS = ('javascript:', 'mailto:', 'tel:')


def extract_links(html: str) -> list[str]:
    """Extract all valid HTTP/HTTPS links from HTML.

    Args:
        html: Raw HTML content to parse.

    Returns:
        List of URL strings found in href attributes. Empty list if no links found.
        Filters out javascript:, mailto:, and tel: protocol URLs.
    """
    matches = HREF_PATTERN.findall(html)
    return [
        url for url in matches
        if not url.startswith(EXCLUDED_PROTOCOLS)
    ]


def extract_forms(html: str, base_url: str = "") -> list[FormData]:
    """Extract all form elements and their input fields from HTML.

    Args:
        html: Raw HTML content to parse.
        base_url: Base URL for resolving relative form actions (unused for now).

    Returns:
        List of FormData objects representing each form found. Empty list if no
        forms found. Each FormData includes action, method, input fields list,
        and file upload detection.
    """
    forms = []
    form_matches = FORM_PATTERN.findall(html)

    for form_attrs, form_body in form_matches:
        # Extract action attribute (default to empty string)
        action_match = ACTION_PATTERN.search(form_attrs)
        action = action_match.group(1) if action_match else ""

        # Extract method attribute (default to GET, uppercase)
        method_match = METHOD_PATTERN.search(form_attrs)
        method = method_match.group(1).upper() if method_match else "GET"

        # Extract all input fields
        inputs = []
        has_file_upload = False

        # Process <input> tags
        for input_attrs in INPUT_PATTERN.findall(form_body):
            name_match = NAME_PATTERN.search(input_attrs)
            type_match = TYPE_PATTERN.search(input_attrs)
            value_match = VALUE_PATTERN.search(input_attrs)

            name = name_match.group(1) if name_match else ""
            input_type = type_match.group(1) if type_match else "text"
            value = value_match.group(1) if value_match else ""

            if input_type == "file":
                has_file_upload = True

            inputs.append({"name": name, "type": input_type, "value": value})

        # Process <select> tags
        for select_attrs in SELECT_PATTERN.findall(form_body):
            name_match = NAME_PATTERN.search(select_attrs)
            name = name_match.group(1) if name_match else ""
            inputs.append({"name": name, "type": "select", "value": ""})

        # Process <textarea> tags
        for textarea_attrs in TEXTAREA_PATTERN.findall(form_body):
            name_match = NAME_PATTERN.search(textarea_attrs)
            name = name_match.group(1) if name_match else ""
            inputs.append({"name": name, "type": "textarea", "value": ""})

        forms.append(
            FormData(
                action=action,
                method=method,
                inputs=inputs,
                has_file_upload=has_file_upload,
            )
        )

    return forms


def extract_buttons(html: str) -> list[ButtonInfo]:
    """Extract all button elements from HTML.

    Args:
        html: Raw HTML content to parse.

    Returns:
        List of ButtonInfo objects representing each button found. Empty list if
        no buttons found. Extracts <button> tags and <input type="submit">/
        <input type="button"> tags.
    """
    buttons = []

    # Extract <button> tags
    for button_attrs, button_text in BUTTON_PATTERN.findall(html):
        # Extract type attribute
        type_match = TYPE_PATTERN.search(button_attrs)
        button_type = type_match.group(1) if type_match else None

        # Extract onclick attribute
        onclick_match = ONCLICK_PATTERN.search(button_attrs)
        onclick = onclick_match.group(1) if onclick_match else None

        # Strip whitespace from text content
        text = button_text.strip() if button_text else None

        buttons.append(
            ButtonInfo(
                text=text,
                type=button_type,
                onclick=onclick,
            )
        )

    # Extract <input type="submit"> and <input type="button"> tags
    for match in INPUT_SUBMIT_PATTERN.finditer(html):
        # Combine all attributes (before and after type attribute)
        all_attrs = match.group(1) + match.group(2)

        # Extract type attribute
        type_match = TYPE_PATTERN.search(all_attrs)
        button_type = type_match.group(1) if type_match else "submit"

        # Extract value attribute (used as button text)
        value_match = VALUE_PATTERN.search(all_attrs)
        text = value_match.group(1) if value_match else None

        # Extract onclick attribute
        onclick_match = ONCLICK_PATTERN.search(all_attrs)
        onclick = onclick_match.group(1) if onclick_match else None

        buttons.append(
            ButtonInfo(
                text=text,
                type=button_type,
                onclick=onclick,
            )
        )

    return buttons

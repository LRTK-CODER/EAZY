"""Crawl result exporter module.

Provides JSON serialization and file export for CrawlResult objects.
"""

from __future__ import annotations

import json
from pathlib import Path

from eazy.models.crawl_types import CrawlResult


class CrawlResultExporter:
    """Exports CrawlResult to JSON string or file.

    Uses Pydantic v2 model_dump for serialization with indent=2
    for human-readable output.
    """

    def to_json(self, result: CrawlResult) -> str:
        """Serialize a CrawlResult to a JSON string.

        Args:
            result: The crawl result to serialize.

        Returns:
            Pretty-printed JSON string (indent=2).
        """
        data = result.model_dump(mode="json")
        return json.dumps(data, indent=2, ensure_ascii=False)

    def save_to_file(self, result: CrawlResult, path: Path) -> None:
        """Save a CrawlResult as a JSON file.

        Args:
            result: The crawl result to save.
            path: File path to write the JSON output.
        """
        path.write_text(self.to_json(result), encoding="utf-8")

"""Skill file loader — parses .skill files and indexes by category."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Type alias
# ---------------------------------------------------------------------------
CATEGORY_TYPE = Literal["attack", "tool", "waf", "verify", "chain", "crypto"]

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class SkillMetadata(BaseModel):
    """Metadata for a single .skill file."""

    name: str = Field(..., description="Skill name derived from filename (no ext)")
    category: CATEGORY_TYPE = Field(..., description="Inferred skill category")
    file_path: str = Field(..., description="Absolute path to the .skill file")


class SkillSection(BaseModel):
    """A single ## section inside a .skill file."""

    title: str = Field(..., description="Section heading text")
    content: str = Field(..., description="Section body text")


class SkillFile(BaseModel):
    """Fully parsed .skill file."""

    metadata: SkillMetadata
    sections: list[SkillSection] = Field(default_factory=list)
    raw_content: str = Field(..., description="Original file content")


# ---------------------------------------------------------------------------
# Category inference maps
# ---------------------------------------------------------------------------
_DIR_CATEGORY_MAP: dict[str, CATEGORY_TYPE] = {
    "attacks": "attack",
    "tools": "tool",
    "waf": "waf",
    "verify": "verify",
    "chains": "chain",
    "crypto": "crypto",
}

_PREFIX_CATEGORY_MAP: list[tuple[str, CATEGORY_TYPE]] = [
    ("waf_", "waf"),
    ("verify_", "verify"),
    ("chain_", "chain"),
    ("crypto_", "crypto"),
    ("tool_", "tool"),
]


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _infer_category(file_path: Path) -> CATEGORY_TYPE:
    """Infer skill category from directory name, then filename prefix."""
    # 1) Directory name takes precedence
    parent_name = file_path.parent.name
    if parent_name in _DIR_CATEGORY_MAP:
        return _DIR_CATEGORY_MAP[parent_name]

    # 2) Filename prefix
    stem = file_path.stem
    for prefix, category in _PREFIX_CATEGORY_MAP:
        if stem.startswith(prefix):
            return category

    # 3) Default
    return "attack"


def _parse_sections(raw: str) -> list[SkillSection]:
    """Parse ## sections from raw .skill content via line iteration."""
    sections: list[SkillSection] = []
    current_title: str | None = None
    current_lines: list[str] = []

    for line in raw.splitlines():
        heading = re.match(r"^##\s+(.+)$", line)
        if heading:
            # Flush previous section
            if current_title is not None:
                sections.append(
                    SkillSection(
                        title=current_title,
                        content="\n".join(current_lines).strip(),
                    )
                )
            current_title = heading.group(1).strip()
            current_lines = []
        elif current_title is not None:
            current_lines.append(line)

    # Flush last section
    if current_title is not None:
        sections.append(
            SkillSection(
                title=current_title,
                content="\n".join(current_lines).strip(),
            )
        )

    return sections


# ---------------------------------------------------------------------------
# SkillLoader
# ---------------------------------------------------------------------------


class SkillLoader:
    """Loads and indexes .skill files from a directory tree."""

    def __init__(self, skills_dir: str = "src/agents/skills/static") -> None:
        self._skills_dir = Path(skills_dir)
        self._index: dict[str, SkillMetadata] = {}
        self._build_index()

    def _build_index(self) -> None:
        """Scan skills_dir recursively and build name → metadata index."""
        self._index.clear()
        if not self._skills_dir.is_dir():
            return
        for path in sorted(self._skills_dir.rglob("*.skill")):
            name = path.stem
            self._index[name] = SkillMetadata(
                name=name,
                category=_infer_category(path),
                file_path=str(path.resolve()),
            )

    def load(self, skill_name: str) -> SkillFile:
        """Load and parse a single skill by name.

        Raises:
            FileNotFoundError: If no skill with that name exists in the index.
        """
        meta = self._index.get(skill_name)
        if meta is None:
            msg = f"Skill not found: {skill_name}"
            raise FileNotFoundError(msg)

        raw = Path(meta.file_path).read_text(encoding="utf-8")
        return SkillFile(
            metadata=meta,
            sections=_parse_sections(raw),
            raw_content=raw,
        )

    def load_by_category(self, category: str) -> list[SkillFile]:
        """Load all skills matching a category."""
        results: list[SkillFile] = []
        for meta in self._index.values():
            if meta.category == category:
                raw = Path(meta.file_path).read_text(encoding="utf-8")
                results.append(
                    SkillFile(
                        metadata=meta,
                        sections=_parse_sections(raw),
                        raw_content=raw,
                    )
                )
        return results

    def list_skills(self) -> list[SkillMetadata]:
        """Return metadata for all indexed skills."""
        return list(self._index.values())

    def reload(self) -> None:
        """Re-scan the skills directory and rebuild the index."""
        self._build_index()

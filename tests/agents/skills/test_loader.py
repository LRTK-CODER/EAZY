"""Tests for SkillLoader — .skill file parsing and category indexing."""

from pathlib import Path

import pytest

from src.agents.skills.loader import SkillFile, SkillLoader, SkillMetadata
from src.agents.skills.selector import SkillSelector

FIXTURES_DIR = str(
    Path(__file__).resolve().parent.parent.parent / "fixtures" / "skills"
)


class TestLoadSkill:
    def test_load_skill_valid(self) -> None:
        loader = SkillLoader(skills_dir=FIXTURES_DIR)
        skill = loader.load("sqli_blind")
        assert isinstance(skill, SkillFile)
        assert skill.metadata.name == "sqli_blind"
        assert len(skill.raw_content) > 0

    def test_load_skill_sections_parsed(self) -> None:
        loader = SkillLoader(skills_dir=FIXTURES_DIR)
        skill = loader.load("sqli_blind")
        titles = [s.title for s in skill.sections]
        assert "Description" in titles
        assert "Payloads" in titles
        assert "Detection" in titles

    def test_load_skill_not_found(self) -> None:
        loader = SkillLoader(skills_dir=FIXTURES_DIR)
        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent_skill")


class TestLoadByCategory:
    def test_load_by_category(self) -> None:
        loader = SkillLoader(skills_dir=FIXTURES_DIR)
        waf_skills = loader.load_by_category("waf")
        assert len(waf_skills) == 1
        assert waf_skills[0].metadata.name == "waf_cloudflare"

    def test_load_by_category_empty(self) -> None:
        loader = SkillLoader(skills_dir=FIXTURES_DIR)
        result = loader.load_by_category("verify")
        assert result == []


class TestListSkills:
    def test_list_skills(self) -> None:
        loader = SkillLoader(skills_dir=FIXTURES_DIR)
        skills = loader.list_skills()
        assert len(skills) == 4
        assert all(isinstance(s, SkillMetadata) for s in skills)
        names = {s.name for s in skills}
        expected = {
            "sqli_blind",
            "waf_cloudflare",
            "crypto_aes_cbc",
            "generic_attack",
        }
        assert names == expected


class TestCategoryInference:
    def test_skill_metadata_category_from_filename(self) -> None:
        loader = SkillLoader(skills_dir=FIXTURES_DIR)
        waf = loader.load("waf_cloudflare")
        crypto = loader.load("crypto_aes_cbc")
        assert waf.metadata.category == "waf"
        assert crypto.metadata.category == "crypto"

    def test_skill_metadata_category_from_directory(self) -> None:
        loader = SkillLoader(skills_dir=FIXTURES_DIR)
        attack = loader.load("generic_attack")
        assert attack.metadata.category == "attack"


class TestReload:
    def test_reload_picks_up_new_file(self, tmp_path: Path) -> None:
        loader = SkillLoader(skills_dir=str(tmp_path))
        assert loader.list_skills() == []

        # Create a new .skill file dynamically
        new_skill = tmp_path / "tool_nmap.skill"
        new_skill.write_text("# Nmap\n\n## Usage\n\nRun nmap scan.\n", encoding="utf-8")

        loader.reload()
        skills = loader.list_skills()
        assert len(skills) == 1
        assert skills[0].name == "tool_nmap"
        assert skills[0].category == "tool"


class TestSkillSelectorInterface:
    def test_skill_selector_interface(self) -> None:
        with pytest.raises(TypeError):
            SkillSelector()  # type: ignore[abstract]

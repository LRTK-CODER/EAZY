"""테스트 공용 픽스처."""

from pathlib import Path

import pytest


@pytest.fixture()
def project_root() -> Path:
    """프로젝트 루트 디렉토리 경로를 반환한다."""
    return Path(__file__).resolve().parent.parent

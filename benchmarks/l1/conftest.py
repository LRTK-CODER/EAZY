"""L1 벤치마크 픽스처.

L1 미니 앱을 in-process로 기동하기 위한 pytest fixture 구조.
구체적인 앱 설계는 Stage SPEC(SPEC-01x ~ SPEC-03x)에서 정의한다.
"""

import pytest


@pytest.fixture()
def l1_app_url() -> str:
    """L1 픽스처 앱의 base URL을 반환한다.

    Returns:
        L1 앱의 base URL. 실제 앱은 Stage SPEC에서 구현한다.
    """
    return "http://localhost:9000"

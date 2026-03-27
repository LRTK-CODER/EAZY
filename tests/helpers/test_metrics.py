"""측정 유틸리티 테스트.

SPEC-000 Feature 1 검증 기준에 대응하는 테스트.
"""

import time

import pytest

from tests.helpers.metrics import MetricsResult, compute_metrics


# ---------------------------------------------------------------------------
# PASS: compute_metrics 호출 시 MetricsResult 반환
# ---------------------------------------------------------------------------
def test_compute_metrics_returns_metrics_result() -> None:
    """compute_metrics 호출 시 MetricsResult 인스턴스를 반환한다."""
    result = compute_metrics([1, 2, 3], [1, 2, 3])
    assert isinstance(result, MetricsResult)


# ---------------------------------------------------------------------------
# PASS: tn 제공 시 Youden's Index 산출
# ---------------------------------------------------------------------------
def test_compute_metrics_with_tn_returns_youdens_index() -> None:
    """tn=N 제공 시 Youden's Index가 float, 미제공 시 None."""
    # tn 미제공 → None
    result_no_tn = compute_metrics([1, 2, 3], [1, 2, 3])
    assert result_no_tn.youdens_index is None

    # tn 제공 → float
    result_with_tn = compute_metrics([1, 2, 3], [1, 2, 3], tn=5)
    assert isinstance(result_with_tn.youdens_index, float)
    # 완전 일치 + tn=5: Sensitivity=1.0, Specificity=5/(5+0)=1.0, J=1.0
    assert result_with_tn.youdens_index == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# PASS: 완전 일치 시 P=1.0, R=1.0, F1=1.0
# ---------------------------------------------------------------------------
def test_perfect_match_returns_all_ones() -> None:
    """predicted와 ground_truth가 완전 일치하면 P=1.0, R=1.0, F1=1.0."""
    result = compute_metrics([1, 2, 3], [1, 2, 3])
    assert result.precision == pytest.approx(1.0)
    assert result.recall == pytest.approx(1.0)
    assert result.f1 == pytest.approx(1.0)
    assert result.true_positives == 3
    assert result.false_positives == 0
    assert result.false_negatives == 0


# ---------------------------------------------------------------------------
# PASS: predicted 빈 리스트 시 P=None, R=0.0, F1=None
# ---------------------------------------------------------------------------
def test_empty_predicted_returns_none_precision_zero_recall() -> None:
    """predicted가 빈 리스트이면 P=None, R=0.0, F1=None."""
    result = compute_metrics([], [1, 2, 3])
    assert result.precision is None
    assert result.recall == pytest.approx(0.0)
    assert result.f1 is None
    assert result.true_positives == 0
    assert result.false_positives == 0
    assert result.false_negatives == 3


# ---------------------------------------------------------------------------
# PASS: ground_truth 빈 리스트 시 P=None, R=None, F1=None
# ---------------------------------------------------------------------------
def test_empty_ground_truth_returns_none_recall() -> None:
    """ground_truth가 빈 리스트이면 P=None, R=None, F1=None."""
    result = compute_metrics([1, 2, 3], [])
    assert result.precision is None
    assert result.recall is None
    assert result.f1 is None


# ---------------------------------------------------------------------------
# PASS: FP만 있으면 P=0.0, R=0.0
# ---------------------------------------------------------------------------
def test_all_fp_returns_zero_precision_zero_recall() -> None:
    """predicted에 FP만 있으면 P=0.0, R=0.0."""
    result = compute_metrics([4, 5, 6], [1, 2, 3])
    assert result.precision == pytest.approx(0.0)
    assert result.recall == pytest.approx(0.0)
    assert result.true_positives == 0
    assert result.false_positives == 3
    assert result.false_negatives == 3


# ---------------------------------------------------------------------------
# PASS: match_fn 커스텀 매칭
# ---------------------------------------------------------------------------
def test_custom_match_fn_used_for_matching() -> None:
    """match_fn 파라미터로 커스텀 매칭 함수를 전달하면 해당 함수로 매칭한다."""
    # 문자열 대소문자 무시 비교
    predicted = ["Apple", "Banana", "Cherry"]
    ground_truth = ["apple", "banana", "durian"]

    result = compute_metrics(
        predicted,
        ground_truth,
        match_fn=lambda a, b: a.lower() == b.lower(),
    )
    # Apple↔apple, Banana↔banana → TP=2, FP=1(Cherry), FN=1(durian)
    assert result.true_positives == 2
    assert result.false_positives == 1
    assert result.false_negatives == 1
    assert result.precision == pytest.approx(2 / 3)
    assert result.recall == pytest.approx(2 / 3)


# ---------------------------------------------------------------------------
# 부정: 타입 불일치 시 TypeError
# ---------------------------------------------------------------------------
def test_type_mismatch_raises_type_error() -> None:
    """predicted와 ground_truth 타입이 불일치하면 TypeError."""
    with pytest.raises(TypeError):
        compute_metrics([1, 2, 3], ["a", "b", "c"])  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# PERF: 10,000개 항목 < 100ms
# ---------------------------------------------------------------------------
def test_compute_metrics_10k_items_under_100ms() -> None:
    """10,000개 항목 기준 100ms 이내에 완료된다."""
    predicted = list(range(10_000))
    ground_truth = list(range(10_000))

    start = time.perf_counter()
    compute_metrics(predicted, ground_truth)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 100, f"10,000개 항목 처리에 {elapsed_ms:.1f}ms 소요 (제한: 100ms)"


# ---------------------------------------------------------------------------
# parametrize 케이스
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "predicted, ground_truth, tn, expected_p, expected_r, expected_f1, expected_youden",
    [
        ([1, 2, 3], [1, 2, 3], None, 1.0, 1.0, 1.0, None),
        ([1, 2, 3], [1, 2, 3], 5, 1.0, 1.0, 1.0, 1.0),
        ([], [1, 2, 3], None, None, 0.0, None, None),
        ([1, 2, 3], [], None, None, None, None, None),
        ([4, 5, 6], [1, 2, 3], None, 0.0, 0.0, 0.0, None),
        ([1, 2, 4], [1, 2, 3], None, 2 / 3, 2 / 3, 2 / 3, None),
    ],
    ids=[
        "perfect_match",
        "perfect_match_with_tn",
        "empty_predicted",
        "empty_ground_truth",
        "all_fp",
        "partial_match",
    ],
)
def test_parametrized_metrics(
    predicted: list[int],
    ground_truth: list[int],
    tn: int | None,
    expected_p: float | None,
    expected_r: float | None,
    expected_f1: float | None,
    expected_youden: float | None,
) -> None:
    """다양한 입력 조합에 대해 올바른 메트릭을 반환한다."""
    result = compute_metrics(predicted, ground_truth, tn=tn)

    if expected_p is None:
        assert result.precision is None
    else:
        assert result.precision == pytest.approx(expected_p, abs=1e-2)

    if expected_r is None:
        assert result.recall is None
    else:
        assert result.recall == pytest.approx(expected_r, abs=1e-2)

    if expected_f1 is None:
        assert result.f1 is None
    else:
        assert result.f1 == pytest.approx(expected_f1, abs=1e-2)

    if expected_youden is None:
        assert result.youdens_index is None
    else:
        assert result.youdens_index == pytest.approx(expected_youden, abs=1e-2)

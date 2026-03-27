"""측정 유틸리티.

SPEC-000 Feature 1: Precision, Recall, F1, Youden's Index 산출.
"""

import operator
from collections import Counter
from typing import Callable, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class MetricsResult(BaseModel):
    """측정 유틸리티 출력."""

    true_positives: int = Field(..., description="정탐 수")
    false_positives: int = Field(..., description="오탐 수")
    false_negatives: int = Field(..., description="미탐 수")
    precision: float | None = Field(..., description="정밀도 (predicted 비어있으면 None)")
    recall: float | None = Field(..., description="재현율 (ground_truth 비어있으면 None)")
    f1: float | None = Field(..., description="F1 스코어")
    true_negatives: int | None = Field(default=None, description="정상 판정 수 (제공된 경우에만)")
    youdens_index: float | None = Field(
        default=None,
        description="Youden's J = Sensitivity + Specificity - 1 (TN 제공 시에만 산출)",
    )


def _validate_types(predicted: list[T], ground_truth: list[T]) -> None:
    """predicted와 ground_truth의 요소 타입이 일치하는지 검사한다."""
    if predicted and ground_truth:
        pred_type = type(predicted[0])
        gt_type = type(ground_truth[0])
        if pred_type != gt_type:
            raise TypeError(
                f"predicted와 ground_truth의 타입이 불일치: "
                f"{pred_type.__name__} vs {gt_type.__name__}"
            )


def _count_tp(
    predicted: list[T],
    ground_truth: list[T],
    match_fn: Callable[[T, T], bool],
) -> int:
    """매칭 함수로 True Positives 수를 산출한다."""
    if match_fn is operator.eq:
        pred_counter: Counter[T] = Counter(predicted)
        gt_counter: Counter[T] = Counter(ground_truth)
        return sum((pred_counter & gt_counter).values())

    gt_matched = [False] * len(ground_truth)
    tp = 0
    for p in predicted:
        for j, g in enumerate(ground_truth):
            if not gt_matched[j] and match_fn(p, g):
                tp += 1
                gt_matched[j] = True
                break
    return tp


def _compute_f1(precision: float, recall: float) -> float:
    """Precision과 Recall로 F1을 산출한다."""
    total = precision + recall
    if total > 0:
        return 2 * precision * recall / total
    return 0.0


def _compute_youdens_index(recall: float, tn: int, fp: int) -> float | None:
    """Youden's Index를 산출한다. TN+FP가 0이면 None."""
    denominator = tn + fp
    if denominator == 0:
        return None
    specificity = tn / denominator
    return recall + specificity - 1.0


def compute_metrics(
    predicted: list[T],
    ground_truth: list[T],
    match_fn: Callable[[T, T], bool] = operator.eq,
    tn: int | None = None,
) -> MetricsResult:
    """predicted와 ground_truth를 비교하여 메트릭을 산출한다.

    Args:
        predicted: Stage가 산출한 결과 리스트.
        ground_truth: 정답 리스트.
        match_fn: 두 항목이 같은지 판정하는 함수 (기본: operator.eq).
        tn: True Negatives 수 (Youden's Index 산출에 필요).

    Returns:
        MetricsResult: TP, FP, FN, Precision, Recall, F1, Youden's Index.

    Raises:
        TypeError: predicted와 ground_truth의 요소 타입이 불일치하면 발생.
    """
    _validate_types(predicted, ground_truth)

    if not ground_truth:
        return MetricsResult(
            true_positives=0,
            false_positives=len(predicted),
            false_negatives=0,
            precision=None,
            recall=None,
            f1=None,
            true_negatives=tn,
        )

    if not predicted:
        return MetricsResult(
            true_positives=0,
            false_positives=0,
            false_negatives=len(ground_truth),
            precision=None,
            recall=0.0,
            f1=None,
            true_negatives=tn,
        )

    tp = _count_tp(predicted, ground_truth, match_fn)
    fp = len(predicted) - tp
    fn = len(ground_truth) - tp

    precision = tp / len(predicted)
    recall = tp / len(ground_truth)
    f1 = _compute_f1(precision, recall)

    youdens_index = _compute_youdens_index(recall, tn, fp) if tn is not None else None

    return MetricsResult(
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        precision=precision,
        recall=recall,
        f1=f1,
        true_negatives=tn,
        youdens_index=youdens_index,
    )

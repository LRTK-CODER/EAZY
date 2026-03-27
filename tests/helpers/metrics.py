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
    # 타입 불일치 검사
    if predicted and ground_truth:
        pred_type = type(predicted[0])
        gt_type = type(ground_truth[0])
        if pred_type != gt_type:
            raise TypeError(
                f"predicted와 ground_truth의 타입이 불일치: "
                f"{pred_type.__name__} vs {gt_type.__name__}"
            )

    # ground_truth 빈 리스트 → 평가 불가
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

    # predicted 빈 리스트
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

    # TP 산출
    if match_fn is operator.eq:
        # Counter 기반 최적화: O(n + m)
        pred_counter: Counter[T] = Counter(predicted)
        gt_counter: Counter[T] = Counter(ground_truth)
        tp = sum((pred_counter & gt_counter).values())
    else:
        # 커스텀 match_fn: greedy 매칭 O(n * m)
        gt_matched = [False] * len(ground_truth)
        tp = 0
        for p in predicted:
            for j, g in enumerate(ground_truth):
                if not gt_matched[j] and match_fn(p, g):
                    tp += 1
                    gt_matched[j] = True
                    break

    fp = len(predicted) - tp
    fn = len(ground_truth) - tp

    precision = tp / len(predicted)
    recall = tp / len(ground_truth)

    if (precision + recall) > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0

    # Youden's Index: J = Sensitivity + Specificity - 1
    youdens_index: float | None = None
    if tn is not None:
        specificity = tn / (tn + fp) if (tn + fp) > 0 else None
        if specificity is not None:
            youdens_index = recall + specificity - 1.0

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

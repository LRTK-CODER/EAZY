"""ScanInterpreter — LLM 1회 호출로 스캔 결과를 종합 해석."""

from __future__ import annotations

import json
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field

from src.agents.core.models import CryptoContext, Technology, WafProfile
from src.agents.scanners.executor import ScanResult


class LLMClient(Protocol):
    """Protocol for LLM client dependency injection."""

    async def interpret(self, prompt: str) -> str: ...


class Finding(BaseModel):
    """Individual security finding from scan interpretation."""

    title: str
    category: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    description: str
    evidence: str | None = None
    affected_endpoint: str | None = None


class ScanInterpreterResult(BaseModel):
    """Structured result of LLM scan interpretation."""

    risk_summary: str
    findings: list[Finding] = Field(default_factory=list)
    waf_profile: WafProfile | None = None
    tech_stack: list[Technology] = Field(default_factory=list)
    crypto_context: CryptoContext | None = None
    raw_results: dict[str, list[dict[str, Any]]] = Field(
        default_factory=dict,
    )
    is_fallback: bool = False


class ScanInterpreter:
    """Interprets scan results via a single LLM call."""

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    async def interpret(self, scan_result: ScanResult) -> ScanInterpreterResult:
        """Interpret scan results into structured security analysis."""
        raw = scan_result.results_by_category
        try:
            prompt = _build_prompt(raw)
            response = await self._llm_client.interpret(prompt)
            return _parse_llm_response(response, raw)
        except Exception:  # noqa: BLE001
            return _build_fallback(raw)


def _build_prompt(
    results_by_category: dict[str, list[dict[str, Any]]],
) -> str:
    """Serialize scan results into an LLM prompt."""
    serialized = json.dumps(results_by_category, indent=2)
    return (
        "You are a security analyst. Analyze the following scan results "
        "and return a JSON object with these fields:\n"
        "- risk_summary: string (concise overall risk assessment)\n"
        "- findings: list of objects with title, category, severity "
        "(critical/high/medium/low/info), description, evidence, "
        "affected_endpoint\n"
        "- waf_profile: object with detected, vendor, ruleset, "
        "confidence (or null)\n"
        "- tech_stack: list of objects with name, version, category\n"
        "- crypto_context: object with detected, algorithm, "
        "encryption_scope (or null)\n\n"
        "Return ONLY valid JSON, no markdown.\n\n"
        f"Scan Results:\n{serialized}"
    )


def _parse_llm_response(
    response: str,
    raw: dict[str, list[dict[str, Any]]],
) -> ScanInterpreterResult:
    """Parse LLM JSON response into ScanInterpreterResult."""
    data = json.loads(response)

    findings = [Finding(**f) for f in data.get("findings", [])]

    waf_data = data.get("waf_profile")
    waf_profile = WafProfile(**waf_data) if waf_data else None

    tech_stack = [Technology(**t) for t in data.get("tech_stack", [])]

    crypto_data = data.get("crypto_context")
    crypto_context = CryptoContext(**crypto_data) if crypto_data else None

    return ScanInterpreterResult(
        risk_summary=data.get("risk_summary", ""),
        findings=findings,
        waf_profile=waf_profile,
        tech_stack=tech_stack,
        crypto_context=crypto_context,
        raw_results=raw,
        is_fallback=False,
    )


def _build_fallback(
    raw: dict[str, list[dict[str, Any]]],
) -> ScanInterpreterResult:
    """Build fallback result when LLM call fails."""
    return ScanInterpreterResult(
        risk_summary="LLM interpretation failed — raw scanner results attached",
        findings=[],
        raw_results=raw,
        is_fallback=True,
    )

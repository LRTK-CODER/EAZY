"""Tests for ScanInterpreter — LLM 종합 해석기."""

import json

import pytest

from src.agents.core.models import CryptoContext, Technology, WafProfile
from src.agents.recon.scan_interpreter import (
    Finding,
    ScanInterpreter,
    ScanInterpreterResult,
)
from src.agents.scanners.executor import ScanResult


class _MockLLMClient:
    """Mock LLM client for testing — only external boundary is mocked."""

    def __init__(self, response: str, *, should_fail: bool = False) -> None:
        self.response = response
        self.should_fail = should_fail
        self.call_count = 0

    async def interpret(self, prompt: str) -> str:
        self.call_count += 1
        if self.should_fail:
            raise RuntimeError("LLM unavailable")
        return self.response


@pytest.fixture()
def sample_scan_result() -> ScanResult:
    """ScanResult with WAF, tech_stack, and crypto data."""
    return ScanResult(
        results_by_category={
            "waf": [
                {
                    "plugin": "waf_detector",
                    "vendor": "Cloudflare",
                    "detected": True,
                    "confidence": 0.95,
                },
            ],
            "tech_stack": [
                {
                    "plugin": "tech_fingerprint",
                    "name": "Django",
                    "version": "4.2",
                    "category": "framework",
                },
            ],
            "crypto": [
                {
                    "plugin": "crypto_scanner",
                    "algorithm": "AES-256-CBC",
                    "detected": True,
                    "scope": "login payload",
                },
            ],
            "endpoint": [
                {
                    "plugin": "endpoint_spider",
                    "url": "/api/login",
                    "method": "POST",
                },
            ],
        },
        plugin_statuses=[],
        elapsed_time=1.5,
    )


def _build_llm_response() -> str:
    """Build a valid LLM JSON response for mock."""
    return json.dumps(
        {
            "risk_summary": "Target uses Cloudflare WAF with Django backend. "
            "AES-256-CBC encryption detected on login payload.",
            "findings": [
                {
                    "title": "WAF Detected",
                    "category": "waf",
                    "severity": "info",
                    "description": "Cloudflare WAF is active",
                    "evidence": "HTTP headers indicate Cloudflare",
                    "affected_endpoint": None,
                },
                {
                    "title": "Weak Crypto Configuration",
                    "category": "crypto",
                    "severity": "medium",
                    "description": "AES-256-CBC mode may be vulnerable"
                    " to padding oracle",
                    "evidence": "Detected in login payload",
                    "affected_endpoint": "/api/login",
                },
            ],
            "waf_profile": {
                "detected": True,
                "vendor": "Cloudflare",
                "ruleset": None,
                "confidence": 0.95,
            },
            "tech_stack": [
                {
                    "name": "Django",
                    "version": "4.2",
                    "category": "framework",
                },
            ],
            "crypto_context": {
                "detected": True,
                "algorithm": "AES-256-CBC",
                "encryption_scope": "login payload",
            },
        }
    )


class TestScanInterpreter:
    """Tests for ScanInterpreter."""

    @pytest.mark.asyncio()
    async def test_interpret_returns_structured_result(
        self, sample_scan_result: ScanResult
    ) -> None:
        mock_llm = _MockLLMClient(response=_build_llm_response())
        interpreter = ScanInterpreter(llm_client=mock_llm)

        result = await interpreter.interpret(sample_scan_result)

        assert isinstance(result, ScanInterpreterResult)

    @pytest.mark.asyncio()
    async def test_interpret_includes_risk_summary(
        self, sample_scan_result: ScanResult
    ) -> None:
        mock_llm = _MockLLMClient(response=_build_llm_response())
        interpreter = ScanInterpreter(llm_client=mock_llm)

        result = await interpreter.interpret(sample_scan_result)

        assert isinstance(result.risk_summary, str)
        assert len(result.risk_summary) > 0

    @pytest.mark.asyncio()
    async def test_interpret_includes_findings(
        self, sample_scan_result: ScanResult
    ) -> None:
        mock_llm = _MockLLMClient(response=_build_llm_response())
        interpreter = ScanInterpreter(llm_client=mock_llm)

        result = await interpreter.interpret(sample_scan_result)

        assert isinstance(result.findings, list)
        assert len(result.findings) >= 1
        assert all(isinstance(f, Finding) for f in result.findings)

    @pytest.mark.asyncio()
    async def test_interpret_updates_waf_profile(
        self, sample_scan_result: ScanResult
    ) -> None:
        mock_llm = _MockLLMClient(response=_build_llm_response())
        interpreter = ScanInterpreter(llm_client=mock_llm)

        result = await interpreter.interpret(sample_scan_result)

        assert result.waf_profile is not None
        assert isinstance(result.waf_profile, WafProfile)
        assert result.waf_profile.vendor == "Cloudflare"

    @pytest.mark.asyncio()
    async def test_interpret_updates_tech_stack(
        self, sample_scan_result: ScanResult
    ) -> None:
        mock_llm = _MockLLMClient(response=_build_llm_response())
        interpreter = ScanInterpreter(llm_client=mock_llm)

        result = await interpreter.interpret(sample_scan_result)

        assert len(result.tech_stack) >= 1
        assert all(isinstance(t, Technology) for t in result.tech_stack)

    @pytest.mark.asyncio()
    async def test_interpret_detects_crypto_context(
        self, sample_scan_result: ScanResult
    ) -> None:
        mock_llm = _MockLLMClient(response=_build_llm_response())
        interpreter = ScanInterpreter(llm_client=mock_llm)

        result = await interpreter.interpret(sample_scan_result)

        assert result.crypto_context is not None
        assert isinstance(result.crypto_context, CryptoContext)
        assert result.crypto_context.detected is True

    @pytest.mark.asyncio()
    async def test_interpret_calls_llm_exactly_once(
        self, sample_scan_result: ScanResult
    ) -> None:
        mock_llm = _MockLLMClient(response=_build_llm_response())
        interpreter = ScanInterpreter(llm_client=mock_llm)

        await interpreter.interpret(sample_scan_result)

        assert mock_llm.call_count == 1

    @pytest.mark.asyncio()
    async def test_interpret_llm_failure_returns_raw_fallback(
        self, sample_scan_result: ScanResult
    ) -> None:
        mock_llm = _MockLLMClient(response="", should_fail=True)
        interpreter = ScanInterpreter(llm_client=mock_llm)

        result = await interpreter.interpret(sample_scan_result)

        assert result.is_fallback is True
        assert result.raw_results == sample_scan_result.results_by_category

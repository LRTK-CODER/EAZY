"""Stage1 Orchestrator — coordinates recon sub-phases into a single pipeline."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from src.agents.core.models import AuthFlow, SessionConfig
from src.agents.recon.attack_surface import AttackSurface, extract_from_kg
from src.agents.recon.auth_flow_mapper import AuthFlowResult, Credentials
from src.agents.recon.crawler import CrawlResult
from src.agents.recon.kg_models import KnowledgeGraphData
from src.agents.recon.knowledge_graph import KnowledgeGraph
from src.agents.recon.scan_interpreter import ScanInterpreterResult
from src.agents.scanners.executor import ScanResult

ProgressCallback = Callable[[str, str], None]

_Phase = Literal["auth_flow", "scanner", "llm_interpret", "crawler", "kg_build"]


class SubPhaseStatus(BaseModel):
    """Status of a single sub-phase execution."""

    phase: _Phase
    success: bool
    elapsed_time: float
    error: str | None = None


class Stage1Result(BaseModel):
    """Final output of the Stage 1 recon pipeline."""

    knowledge_graph: KnowledgeGraph
    attack_surface: AttackSurface
    auth_result: AuthFlowResult | None = None
    scan_result: ScanInterpreterResult | None = None
    crawl_result: CrawlResult | None = None
    sub_phase_statuses: list[SubPhaseStatus] = Field(default_factory=list)
    elapsed_time: float
    partial_failure: bool = False
    model_config = ConfigDict(arbitrary_types_allowed=True)


class Stage1Orchestrator:
    """Coordinates Stage 1 recon sub-phases into a pipeline."""

    def __init__(
        self,
        auth_mapper: Any,
        scanner_executor: Any,
        scan_interpreter: Any,
        crawler: Any,
        kg_builder: Any,
        workspace_path: Path | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        self._auth_mapper = auth_mapper
        self._scanner_executor = scanner_executor
        self._scan_interpreter = scan_interpreter
        self._crawler = crawler
        self._kg_builder = kg_builder
        self._workspace_path = workspace_path
        self._progress = progress_callback

    async def run(
        self,
        config: SessionConfig,
        credentials: Credentials,
    ) -> Stage1Result:
        """Execute the full Stage 1 recon pipeline."""
        start = time.monotonic()
        statuses: list[SubPhaseStatus] = []
        partial_failure = False

        # Phase 1: auth + scanner concurrently
        auth_result, scan_result = await self._run_phase1(
            config,
            credentials,
            statuses,
        )
        if auth_result is None or scan_result is None:
            partial_failure = True

        # Phase 2: LLM interpret (needs scan_result)
        scan_interp: ScanInterpreterResult | None = None
        if scan_result is not None:
            scan_interp = await self._run_phase(
                "llm_interpret",
                self._scan_interpreter.interpret(scan_result),
                statuses,
            )
            if scan_interp is None:
                partial_failure = True
        else:
            partial_failure = True
            scan_interp = ScanInterpreterResult(
                risk_summary="Scanner failed — no data",
                is_fallback=True,
            )

        # Phase 3: Crawler (needs auth to have completed, not necessarily succeeded)
        crawl_result = await self._run_phase(
            "crawler",
            self._crawler.crawl(config.target_url),
            statuses,
        )
        if crawl_result is None:
            partial_failure = True
            crawl_result = CrawlResult(is_fallback=True, error="Crawler failed")

        # Phase 4: KG Build
        fallback_auth = auth_result or AuthFlowResult(
            auth_flow=AuthFlow(session_mechanism="cookie"),
            success=False,
            login_url=config.target_url,
            is_fallback=True,
        )
        fallback_interp = scan_interp or ScanInterpreterResult(
            risk_summary="No scan data",
            is_fallback=True,
        )
        kg = await self._run_phase(
            "kg_build",
            self._kg_builder.build(
                crawl_result,
                fallback_interp,
                fallback_auth,
                workspace_path=self._workspace_path,
            ),
            statuses,
        )
        if kg is None:
            partial_failure = True
            kg = KnowledgeGraph(target_url=config.target_url)

        # Extract attack surface from KG
        attack_surface = self._extract_attack_surface(kg, config.target_url)

        elapsed = time.monotonic() - start
        return Stage1Result(
            knowledge_graph=kg,
            attack_surface=attack_surface,
            auth_result=auth_result,
            scan_result=scan_interp,
            crawl_result=crawl_result,
            sub_phase_statuses=statuses,
            elapsed_time=elapsed,
            partial_failure=partial_failure,
        )

    # ── Phase helpers ──────────────────────────────────────────────

    async def _run_phase1(
        self,
        config: SessionConfig,
        credentials: Credentials,
        statuses: list[SubPhaseStatus],
    ) -> tuple[AuthFlowResult | None, ScanResult | None]:
        """Run auth_flow and scanner concurrently."""
        auth_coro = self._run_phase(
            "auth_flow",
            self._auth_mapper.map_auth_flow(config.target_url, credentials),
            statuses,
        )
        scanner_coro = self._run_phase(
            "scanner",
            self._scanner_executor.execute(config.target_url),
            statuses,
        )
        results = await asyncio.gather(auth_coro, scanner_coro)
        return results[0], results[1]

    async def _run_phase(
        self,
        phase: _Phase,
        coro: Any,
        statuses: list[SubPhaseStatus],
    ) -> Any:
        """Execute a phase with timing, error handling, and progress reporting."""
        self._report(phase, "started")
        phase_start = time.monotonic()
        try:
            result = await coro
            elapsed = time.monotonic() - phase_start
            statuses.append(
                SubPhaseStatus(phase=phase, success=True, elapsed_time=elapsed),
            )
            self._report(phase, "completed")
            return result  # noqa: TRY300
        except Exception as exc:  # noqa: BLE001
            elapsed = time.monotonic() - phase_start
            statuses.append(
                SubPhaseStatus(
                    phase=phase,
                    success=False,
                    elapsed_time=elapsed,
                    error=str(exc),
                ),
            )
            self._report(phase, "failed")
            return None

    def _report(self, phase: str, status: str) -> None:
        if self._progress is not None:
            self._progress(phase, status)

    @staticmethod
    def _extract_attack_surface(
        kg: KnowledgeGraph,
        target_url: str,
    ) -> AttackSurface:
        """Build KnowledgeGraphData from KG and extract AttackSurface."""
        raw = json.loads(kg.to_json())
        kg_data = KnowledgeGraphData.model_validate(raw["graph"])
        return extract_from_kg(kg_data)

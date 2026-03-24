"""
Mixture-of-Agents pipeline — fires specialist models in parallel and
collects their results, with per-token streaming callbacks.
"""

import asyncio
import time
from typing import Callable, Awaitable

from logger import logger
from providers.base import BaseProvider, Specialist, SpecialistResult
from providers.factory import get_provider

# Type alias for the per-token callback: (model, provider, token) -> None
TokenCallback = Callable[[str, str, str], Awaitable[None]]


class MoAPipeline:
    """Orchestrates parallel, serial, and debate specialist invocations."""

    # ------------------------------------------------------------------
    # Parallel mode
    # ------------------------------------------------------------------

    async def run_parallel(
        self,
        query: str,
        specialists: list[Specialist],
        chairman_config: dict,
        on_token: TokenCallback | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> list[SpecialistResult]:
        """
        Fire all *specialists* simultaneously and collect their results.

        Args:
            query: The user's input query.
            specialists: List of specialist configurations to invoke.
            chairman_config: Chairman model configuration (reserved for
                downstream aggregation — not used inside this method).
            on_token: Optional async callback ``(model, provider, token)``
                invoked for every content token as it streams.
            history: Optional prior conversation messages to prepend to
                each specialist's prompt for multi-turn support.

        Returns:
            A ``SpecialistResult`` for every specialist, in the same order
            as the input list.  Failed specialists have ``error`` set and
            an empty ``content``.
        """
        tasks = [
            self._run_specialist(specialist, query, on_token=on_token, history=history)
            for specialist in specialists
        ]
        results: list[SpecialistResult | BaseException] = await asyncio.gather(
            *tasks, return_exceptions=True
        )

        return self._normalise(results, specialists)

    # ------------------------------------------------------------------
    # Serial mode
    # ------------------------------------------------------------------

    async def run_serial(
        self,
        query: str,
        specialists: list[Specialist],
        chairman_config: dict,
        on_token: TokenCallback | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> list[SpecialistResult]:
        """
        Run specialists one at a time, each receiving the previous
        specialist's output as additional context.

        Args:
            query: The user's input query.
            specialists: List of specialist configurations to invoke in order.
            chairman_config: Reserved for downstream aggregation.
            on_token: Optional per-token streaming callback.
            history: Optional prior conversation messages.

        Returns:
            A ``SpecialistResult`` for every specialist in order.
        """
        results: list[SpecialistResult] = []
        previous_content: str | None = None

        for specialist in specialists:
            # Build messages: history + query + previous specialist output (if any)
            messages = self._build_messages(query, history, previous_content)
            result = await self._run_specialist(
                specialist, query, on_token=on_token, history=history,
                extra_context=previous_content,
            )
            results.append(result)
            if result.error is None:
                previous_content = result.content

        return results

    # ------------------------------------------------------------------
    # Debate mode
    # ------------------------------------------------------------------

    async def run_debate(
        self,
        query: str,
        specialists: list[Specialist],
        chairman_config: dict,
        on_token: TokenCallback | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> list[SpecialistResult]:
        """
        Two-round debate pipeline.

        - Round 1: All specialists answer the original query in parallel.
        - Round 2: Each specialist receives all Round 1 responses and
          is asked to critique/improve its answer.

        Args:
            query: The user's input query.
            specialists: List of specialist configurations.
            chairman_config: Reserved for downstream aggregation.
            on_token: Optional per-token streaming callback.
            history: Optional prior conversation messages.

        Returns:
            Round 2 ``SpecialistResult`` list (same order as input).
        """
        # Round 1 — parallel
        round1_tasks = [
            self._run_specialist(specialist, query, on_token=on_token, history=history)
            for specialist in specialists
        ]
        round1_raw: list[SpecialistResult | BaseException] = await asyncio.gather(
            *round1_tasks, return_exceptions=True
        )
        round1 = self._normalise(round1_raw, specialists)

        # Build a summary of all Round 1 responses for the debate prompt
        debate_context = self._build_debate_context(query, round1)

        # Round 2 — each specialist critiques & improves
        round2_tasks = [
            self._run_specialist(
                specialist, query, on_token=on_token, history=history,
                extra_context=debate_context,
            )
            for specialist in specialists
        ]
        round2_raw: list[SpecialistResult | BaseException] = await asyncio.gather(
            *round2_tasks, return_exceptions=True
        )
        return self._normalise(round2_raw, specialists)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_messages(
        query: str,
        history: list[dict[str, str]] | None,
        extra_context: str | None,
    ) -> list[dict[str, str]]:
        """Assemble the message list for a specialist invocation."""
        messages: list[dict[str, str]] = []
        if history:
            messages.extend(history)
        if extra_context:
            messages.append({
                "role": "user",
                "content": (
                    f"Previous context:\n{extra_context}\n\n"
                    f"Now answer the following:\n{query}"
                ),
            })
        else:
            messages.append({"role": "user", "content": query})
        return messages

    @staticmethod
    def _build_debate_context(query: str, round1: list[SpecialistResult]) -> str:
        """Build the critique prompt injected in Round 2 of debate mode."""
        sections = []
        for r in round1:
            if r.error is None:
                sections.append(f"--- {r.model} ({r.provider}) ---\n{r.content}")
        joined = "\n\n".join(sections)
        return (
            f"The following are Round 1 responses to the question: {query!r}\n\n"
            f"{joined}\n\n"
            "Now critique these responses, correct any errors, and provide "
            "your improved final answer."
        )

    @staticmethod
    def _normalise(
        results: list[SpecialistResult | BaseException],
        specialists: list[Specialist],
    ) -> list[SpecialistResult]:
        """Convert any bare exceptions into SpecialistResult with error set."""
        final: list[SpecialistResult] = []
        for idx, result in enumerate(results):
            if isinstance(result, SpecialistResult):
                final.append(result)
            else:
                spec = specialists[idx]
                final.append(
                    SpecialistResult(
                        model=spec.model,
                        provider=spec.provider,
                        content="",
                        tokens_per_sec=0.0,
                        latency_ms=0,
                        token_count=0,
                        error=str(result),
                    )
                )
        return final

    @staticmethod
    async def _run_specialist(
        specialist: Specialist,
        query: str,
        on_token: TokenCallback | None = None,
        history: list[dict[str, str]] | None = None,
        extra_context: str | None = None,
    ) -> SpecialistResult:
        """
        Run a single specialist: stream its response token-by-token,
        invoke *on_token* for each chunk, measure timing, and return a
        populated ``SpecialistResult``.
        """
        try:
            provider: BaseProvider = get_provider(specialist.provider)
            messages = MoAPipeline._build_messages(query, history, extra_context)

            chunks: list[str] = []
            start_time = time.perf_counter()

            logger.info(
                "specialist_start",
                model=specialist.model,
                provider=specialist.provider,
                query_len=len(query),
            )

            async for chunk in provider.stream(
                model=specialist.model,
                messages=messages,
                system_prompt=specialist.system_prompt,
                temperature=specialist.temperature,
                max_tokens=specialist.max_tokens,
            ):
                chunks.append(chunk)
                if on_token is not None:
                    await on_token(specialist.model, specialist.provider, chunk)

            end_time = time.perf_counter()
            elapsed = end_time - start_time
            chunk_count = len(chunks)
            tokens_per_sec = chunk_count / elapsed if elapsed > 0 else 0.0
            latency_ms = int(elapsed * 1000)

            logger.info(
                "specialist_done",
                model=specialist.model,
                provider=specialist.provider,
                latency_ms=latency_ms,
                token_count=chunk_count,
            )

            return SpecialistResult(
                model=specialist.model,
                provider=specialist.provider,
                content="".join(chunks),
                tokens_per_sec=round(tokens_per_sec, 2),
                latency_ms=latency_ms,
                token_count=chunk_count,
            )

        except Exception as e:
            logger.error(
                "specialist_done",
                model=specialist.model,
                provider=specialist.provider,
                latency_ms=0,
                token_count=0,
                error=str(e),
            )
            return SpecialistResult(
                model=specialist.model,
                provider=specialist.provider,
                content="",
                tokens_per_sec=0.0,
                latency_ms=0,
                token_count=0,
                error=str(e),
            )

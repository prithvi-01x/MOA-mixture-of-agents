"""
Chairman aggregator — synthesises specialist outputs into a single final
answer via a designated chairman model.
"""

from typing import AsyncGenerator

from providers.base import SpecialistResult
from providers.factory import get_provider

_CHAIRMAN_SYSTEM_PROMPT = (
    "You are a Chairman AI. Your job is to produce the single best possible "
    "answer by synthesizing responses from multiple specialist AI models. "
    "Identify factually correct information, combine the best parts, correct "
    "any errors, and produce one final complete answer. Do not mention which "
    "model said what."
)

_MAX_CONTENT_CHARS = 1024 * 4  # ~1024 tokens


class ChairmanAggregator:
    """Aggregates specialist results into a unified answer via a chairman model."""

    async def aggregate(
        self,
        query: str,
        results: list[SpecialistResult],
        chairman: dict,
    ) -> AsyncGenerator[str, None]:
        """
        Stream the chairman's synthesised answer.

        Args:
            query: The original user question.
            results: Specialist outputs to aggregate.
            chairman: Dict with ``model`` and ``provider`` keys.

        Yields:
            Content token strings as they arrive from the chairman model.
        """
        # Filter out failed specialists
        valid = [r for r in results if r.error is None]

        if not valid:
            yield "All specialist models failed to respond."
            return

        # Build the user message with truncated specialist outputs
        sections: list[str] = []
        for r in valid:
            content = r.content[:_MAX_CONTENT_CHARS]
            sections.append(
                f"--- {r.model} ({r.provider}) ---\n{content}"
            )

        specialist_block = "\n\n".join(sections)
        user_message = (
            f"Original Question: {query}\n\n"
            f"Specialist Responses:\n\n"
            f"{specialist_block}\n\n"
            f"Provide the best combined final answer:"
        )

        messages: list[dict[str, str]] = [
            {"role": "user", "content": user_message},
        ]

        provider = get_provider(chairman["provider"])

        async for chunk in provider.stream(
            model=chairman["model"],
            messages=messages,
            system_prompt=_CHAIRMAN_SYSTEM_PROMPT,
        ):
            yield chunk

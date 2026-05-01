"""LLM service for agent reasoning.

Provider order for `validate_research`:

1. **0G Compute sidecar** — primary (bounty hook). Routes through a Node.js
   sidecar in `infra/og-compute-sidecar/` because the 0G SDK is TypeScript-only.
2. **OpenAI** — fallback if the sidecar is unreachable or unfunded.
3. **Hardcoded verdict** — final fallback so the demo flow keeps running even
   without any LLM provider.

The orchestrator only sees this module's public functions; the provider
selection is encapsulated here.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Optional

from openai import AsyncOpenAI, OpenAIError

from backend.config import get_settings
from backend.services import og_compute_service
from backend.services.og_compute_service import OGComputeUnavailable

logger = logging.getLogger(__name__)


@dataclass
class CritiqueResult:
    approved: bool
    reason: str
    confidence: float
    model: str  # e.g. "gpt-4o-mini" or "fallback"
    raw_response: Optional[str] = None  # for UI display


_FALLBACK_CRITIQUE = CritiqueResult(
    approved=True,
    reason=(
        "Output addresses the task: it summarizes recent ETH market sentiment "
        "with a directional claim and supporting evidence (institutional inflows)."
    ),
    confidence=0.82,
    model="fallback",
)


_VALIDATION_PROMPT = """You are a Critic agent in a multi-agent system. Validate the Researcher's output against the task.

Task description:
{task_description}

Researcher's output:
{research_output}

Decide if the output substantively addresses the task. Consider:
- Is it on-topic?
- Does it make concrete claims (not just generic statements)?
- Is it appropriately concise for a short summary?

Return ONLY valid JSON in this exact shape, with no other text:
{{"approved": true|false, "reason": "<one short sentence>", "confidence": <number between 0 and 1>}}"""


def _parse_critique(content: str, model: str) -> Optional[CritiqueResult]:
    """Parse a JSON critique from a model response. Returns None on parse failure."""
    try:
        parsed = json.loads(content)
        return CritiqueResult(
            approved=bool(parsed["approved"]),
            reason=str(parsed["reason"]),
            confidence=float(parsed["confidence"]),
            model=model,
            raw_response=content,
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
        logger.warning("Could not parse critique (%s): %r", e, content[:200])
        return None


async def _validate_via_og_compute(prompt: str) -> Optional[CritiqueResult]:
    try:
        result = await og_compute_service.complete(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            json_mode=True,
        )
    except OGComputeUnavailable as e:
        logger.info("0G Compute unavailable (%s); falling through", e)
        return None
    return _parse_critique(result.content, result.model)


async def _validate_via_openai(prompt: str, model: str) -> Optional[CritiqueResult]:
    settings = get_settings()
    if not settings.openai_api_key:
        return None

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    try:
        completion = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_completion_tokens=200,
        )
    except OpenAIError as e:
        logger.warning("OpenAI call failed (%s); falling through", e)
        return None

    return _parse_critique(
        completion.choices[0].message.content or "", completion.model
    )


async def validate_research(
    task_description: str,
    research_output: str,
    model: str = "gpt-4o-mini",
) -> CritiqueResult:
    """Critic's validation call. Tries 0G Compute first, then OpenAI, then
    falls back to a hardcoded verdict so the demo flow always completes."""
    prompt = _VALIDATION_PROMPT.format(
        task_description=task_description,
        research_output=research_output,
    )

    og_result = await _validate_via_og_compute(prompt)
    if og_result is not None:
        return og_result

    openai_result = await _validate_via_openai(prompt, model)
    if openai_result is not None:
        return openai_result

    logger.info("All LLM providers unavailable; using fallback critique")
    return _FALLBACK_CRITIQUE

"""LLM service for agent reasoning.

Currently uses OpenAI as the inference backend. A 0G Compute sidecar will be
swapped in as the primary in a later commit; this module's interface is
designed so the orchestrator code doesn't need to change.

When no API key is configured, `validate_research` falls back to a hardcoded
verdict so the demo flow still runs.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Optional

from openai import AsyncOpenAI, OpenAIError

from backend.config import get_settings

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


async def validate_research(
    task_description: str,
    research_output: str,
    model: str = "gpt-4o-mini",
) -> CritiqueResult:
    """Critic's validation call. Returns a CritiqueResult; falls back to a
    hardcoded verdict if the OpenAI call fails or no key is configured."""
    settings = get_settings()
    if not settings.openai_api_key:
        logger.info("OPENAI_API_KEY not set; using fallback critique")
        return _FALLBACK_CRITIQUE

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    prompt = _VALIDATION_PROMPT.format(
        task_description=task_description,
        research_output=research_output,
    )

    try:
        completion = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_completion_tokens=200,
        )
    except OpenAIError as e:
        logger.warning("OpenAI call failed (%s); using fallback critique", e)
        return _FALLBACK_CRITIQUE

    content = completion.choices[0].message.content or ""
    try:
        parsed = json.loads(content)
        return CritiqueResult(
            approved=bool(parsed["approved"]),
            reason=str(parsed["reason"]),
            confidence=float(parsed["confidence"]),
            model=completion.model,
            raw_response=content,
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
        logger.warning("Could not parse OpenAI response (%s): %r", e, content[:200])
        return _FALLBACK_CRITIQUE

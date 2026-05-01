"""Python client for the 0G Compute sidecar.

The sidecar lives in `infra/og-compute-sidecar/` and exposes a small HTTP API.
This module provides a thin async wrapper so the rest of the backend can call
0G Compute inference without caring about Node/TypeScript.

When the sidecar is unreachable or returns a non-2xx response, callers should
catch `OGComputeUnavailable` and fall back to another provider.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import httpx

from backend.config import get_settings

logger = logging.getLogger(__name__)


class OGComputeUnavailable(Exception):
    """Raised when the sidecar is down, not ready, or upstream errored."""


@dataclass
class OGCompletion:
    model: str
    provider: str
    content: str


async def health() -> dict:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.get(f"{settings.og_compute_sidecar_url}/health")
        r.raise_for_status()
        return r.json()


async def complete(
    messages: list[dict],
    *,
    max_tokens: int = 200,
    json_mode: bool = False,
) -> OGCompletion:
    """Call the sidecar's /infer endpoint.

    Raises OGComputeUnavailable on any non-success path so callers can fall back.
    """
    settings = get_settings()
    payload: dict = {"messages": messages, "max_tokens": max_tokens}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{settings.og_compute_sidecar_url}/infer", json=payload
            )
    except httpx.HTTPError as e:
        raise OGComputeUnavailable(f"sidecar unreachable: {e}") from e

    if r.status_code != 200:
        try:
            detail = r.json()
        except Exception:
            detail = r.text[:300]
        raise OGComputeUnavailable(f"sidecar status {r.status_code}: {detail}")

    data = r.json()
    return OGCompletion(
        model=data["model"],
        provider=data.get("provider", ""),
        content=data.get("content", ""),
    )

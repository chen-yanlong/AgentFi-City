"""Python client for the 0G Storage endpoints on the sidecar.

Mirrors `og_compute_service`: thin async wrapper that raises a typed exception
on any failure path so callers can fall back gracefully.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Optional

import httpx

from backend.config import get_settings

logger = logging.getLogger(__name__)


class OGStorageUnavailable(Exception):
    """Raised when the sidecar is down, unfunded, or the upload/download fails."""


@dataclass
class UploadResult:
    root_hash: str
    tx_hash: Optional[str]
    indexer_url: Optional[str]


def storage_explorer_url(root_hash: str) -> str:
    """Best-effort link to the 0G Storage explorer for a given root hash."""
    return f"https://storagescan-galileo.0g.ai/tx/{root_hash}"


async def upload(content: str) -> UploadResult:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                f"{settings.og_compute_sidecar_url}/storage/upload",
                json={"content": content},
            )
    except httpx.HTTPError as e:
        raise OGStorageUnavailable(f"sidecar unreachable: {e}") from e

    if r.status_code != 200:
        try:
            detail = r.json()
        except Exception:
            detail = r.text[:300]
        raise OGStorageUnavailable(f"upload status {r.status_code}: {detail}")

    data = r.json()
    return UploadResult(
        root_hash=data["rootHash"],
        tx_hash=data.get("txHash"),
        indexer_url=data.get("indexer_url"),
    )


async def download(root_hash: str) -> str:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.get(
                f"{settings.og_compute_sidecar_url}/storage/download/{root_hash}"
            )
    except httpx.HTTPError as e:
        raise OGStorageUnavailable(f"sidecar unreachable: {e}") from e

    if r.status_code != 200:
        raise OGStorageUnavailable(f"download status {r.status_code}: {r.text[:300]}")

    return r.json().get("content", "")


async def upload_json(obj: dict) -> UploadResult:
    return await upload(json.dumps(obj, separators=(",", ":")))

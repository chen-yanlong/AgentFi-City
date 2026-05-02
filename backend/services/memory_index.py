"""Local pointer index for agent memories stored on 0G.

The actual memory content lives on 0G Storage (content-addressable). This
module maintains a small JSON file mapping `agent_id → [{root_hash, task_id,
timestamp}, ...]` so agents can ask "what are my past memories?" and then
fetch each blob from 0G via the sidecar.

A production system would store this index on 0G KV (the SDK exposes that)
keyed by agent_id; we use a local file for hackathon scope.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from backend.services import og_storage_service
from backend.services.og_storage_service import OGStorageUnavailable

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = REPO_ROOT / "data" / "memory_index.json"


@dataclass
class MemoryPointer:
    root_hash: str
    task_id: str
    timestamp: str
    real_upload: bool  # was this a real 0G upload, or a fake key?


def _load_index() -> dict[str, list[dict]]:
    if not INDEX_PATH.exists():
        return {}
    try:
        return json.loads(INDEX_PATH.read_text())
    except json.JSONDecodeError:
        logger.warning("memory_index.json is corrupted; resetting")
        return {}


def _save_index(idx: dict[str, list[dict]]) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(idx, indent=2))


def record(agent_id: str, pointer: MemoryPointer) -> None:
    idx = _load_index()
    idx.setdefault(agent_id, []).append(asdict(pointer))
    _save_index(idx)


def list_pointers(agent_id: str, limit: int = 5) -> list[MemoryPointer]:
    """Returns most recent pointers (newest last), limited by `limit`."""
    idx = _load_index()
    raw = idx.get(agent_id, [])
    return [MemoryPointer(**p) for p in raw[-limit:]]


@dataclass
class MemoryRecord:
    pointer: MemoryPointer
    content: Optional[dict]  # None if download failed or pointer is fake


async def load_memories(agent_id: str, limit: int = 5) -> list[MemoryRecord]:
    """Return past memories for an agent, fetching content from 0G when possible.

    Pointers with `real_upload=False` are returned without a content fetch
    (they're fake keys that don't exist on 0G). Real pointers attempt a 0G
    download; failures fall through with `content=None` rather than raising.
    """
    pointers = list_pointers(agent_id, limit=limit)
    out: list[MemoryRecord] = []
    for p in pointers:
        if not p.real_upload:
            out.append(MemoryRecord(pointer=p, content=None))
            continue
        try:
            raw = await og_storage_service.download(p.root_hash)
            try:
                content = json.loads(raw)
            except json.JSONDecodeError:
                content = {"_raw": raw}
            out.append(MemoryRecord(pointer=p, content=content))
        except OGStorageUnavailable as e:
            logger.info(
                "Could not fetch memory %s for %s (%s)", p.root_hash[:10], agent_id, e
            )
            out.append(MemoryRecord(pointer=p, content=None))
    return out


def reset() -> None:
    """Drop the entire index — useful for resetting demo state between runs."""
    if INDEX_PATH.exists():
        INDEX_PATH.unlink()

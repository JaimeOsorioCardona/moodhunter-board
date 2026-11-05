"""Summary application service: builds minimized snapshots, manages caching, and coordinates LLM gateway."""

import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any

from app.application.ports import ILLMGateway, IUnitOfWork
from app.infrastructure.db.models import RequestModel


class SummaryService:
    # 5-minute in-memory cache keyed by snapshot hash: (expire_timestamp, result_dict)
    _cache: dict[str, tuple[float, dict[str, Any]]] = {}

    def __init__(self, uow: IUnitOfWork, gateway: ILLMGateway, cache_ttl_seconds: float = 300.0):
        self.uow = uow
        self.gateway = gateway
        self.cache_ttl_seconds = cache_ttl_seconds

    async def get_or_generate_summary(self, force_refresh: bool = False) -> dict[str, Any]:
        """Generate or retrieve cached executive summary for current board status."""
        snapshot = await self.build_snapshot()
        snapshot_hash = self._compute_hash(snapshot)
        now = time.monotonic()

        # Check in-memory cache
        if not force_refresh and snapshot_hash in self._cache:
            expire_at, cached_result = self._cache[snapshot_hash]
            if now < expire_at:
                result = dict(cached_result)
                result["cached"] = True
                return result

        # Call gateway (LLM or fallback)
        result = await self.gateway.generate_summary(snapshot)

        # Store in cache
        self._cache[snapshot_hash] = (now + self.cache_ttl_seconds, result)
        return result

    async def build_snapshot(self) -> dict[str, Any]:
        """Construct minimized, privacy-preserving operational snapshot.

        Calculates counts and stagnation metrics in backend to minimize token usage and LLM arithmetic errors.
        """
        async with self.uow:
            counts = await self.uow.requests.count_by_status()
            all_requests = await self.uow.requests.list()

        now_utc = datetime.now(timezone.utc)

        # Sort: paused first, then oldest updated, up to 50 items
        def sort_key(req: RequestModel) -> tuple[int, datetime]:
            is_paused = 0 if (req.status and req.status.code == "paused") else 1
            # Make sure updated_at is timezone-aware
            updated = req.updated_at
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=timezone.utc)
            return (is_paused, updated)

        sorted_requests = sorted(all_requests, key=sort_key)[:50]

        items = []
        for r in sorted_requests:
            updated = r.updated_at
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=timezone.utc)
            days_inactive = max(0, (now_utc - updated).days)

            items.append(
                {
                    "ref": r.public_id[:8],
                    "title": r.title[:80],
                    "status": r.status.code if r.status else "created",
                    "updated": updated.strftime("%Y-%m-%d"),
                    "days_without_update": days_inactive,
                }
            )

        return {
            "generated_at": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "counts": counts,
            "items": items,
        }

    def _compute_hash(self, snapshot: dict[str, Any]) -> str:
        """Compute stable SHA-256 hash of snapshot content for caching."""
        # Exclude generated_at timestamp for stable caching when data has not changed
        content = {
            "counts": snapshot.get("counts", {}),
            "items": snapshot.get("items", []),
        }
        raw_json = json.dumps(content, sort_keys=True)
        return hashlib.sha256(raw_json.encode("utf-8")).hexdigest()

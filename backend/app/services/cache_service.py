"""
Redis caching service — simulation results (1hr TTL), market data (15min TTL).
"""

from __future__ import annotations

import json
from typing import Optional

import redis.asyncio as redis

from backend.app.config import get_settings

settings = get_settings()

# TTL constants
SIMULATION_TTL = 3600      # 1 hour
MARKET_DATA_TTL = 900      # 15 minutes
DEFAULT_TTL = 1800         # 30 minutes


class CacheService:
    """Async Redis caching service."""

    def __init__(self):
        self._redis: Optional[redis.Redis] = None

    async def connect(self):
        """Initialize Redis connection."""
        self._redis = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    async def disconnect(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()

    async def get(self, key: str) -> Optional[dict]:
        """Get a cached value by key."""
        if not self._redis:
            return None
        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
        except Exception:
            return None
        return None

    async def set(self, key: str, value: dict, ttl: int = DEFAULT_TTL) -> bool:
        """Set a cached value with TTL."""
        if not self._redis:
            return False
        try:
            await self._redis.set(key, json.dumps(value, default=str), ex=ttl)
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """Delete a cached key."""
        if not self._redis:
            return False
        try:
            await self._redis.delete(key)
            return True
        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        if not self._redis:
            return False
        try:
            return bool(await self._redis.exists(key))
        except Exception:
            return False

    def simulation_key(self, user_id: int, sim_type: str, params_hash: str) -> str:
        """Generate cache key for simulation results."""
        return f"sim:{user_id}:{sim_type}:{params_hash}"

    def market_key(self, data_type: str) -> str:
        """Generate cache key for market data."""
        return f"market:{data_type}"


# Global cache service instance
cache_service = CacheService()

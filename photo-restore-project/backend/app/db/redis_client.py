"""Pool de conexiones a Redis (cache, sesiones, rate limiting).

Placeholder inicial — el pool está definido pero aún no se usa lógica encima.
"""

import redis

from app.core.config import settings

redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)


def get_redis() -> redis.Redis:
    """Devuelve un cliente Redis que reutiliza el pool global."""
    return redis.Redis(connection_pool=redis_pool)

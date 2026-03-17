import json
import redis

from app.core.config import settings

_redis = redis.Redis.from_url(settings.REDIS_URL)


def publish_log(execution_id: str, message: str):
    _redis.publish(f"exec:{execution_id}:logs", json.dumps({"msg": message}))

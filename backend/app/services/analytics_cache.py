import time

class AnalyticsCache:
    def __init__(self):
        self._cache = {}

    def get(self, key: str):
        item = self._cache.get(key)
        if item:
            val, expiry = item
            if expiry is None or time.time() < expiry:
                return val
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value, ttl_seconds: int = 300):
        expiry = time.time() + ttl_seconds if ttl_seconds else None
        self._cache[key] = (value, expiry)

    def invalidate_all(self):
        self._cache.clear()

analytics_cache = AnalyticsCache()

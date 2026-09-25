"""
WhatsApp Business Agent Cache
Simple caching layer with Redis fallback to in-memory.
"""

import os
import time
import json
from typing import Any, Optional, Union
from datetime import datetime, timedelta

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

class WhatsAppBusinessCache:
    def __init__(self, namespace: str = "default", redis_url: Optional[str] = None):
        """
        Initialize cache.
        
        Args:
            namespace: Unique namespace for this business (e.g., business_id)
            redis_url: Redis URL (e.g., redis://localhost:6379). If None, uses REDIS_URL env var.
        """
        self.namespace = namespace
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._use_redis = REDIS_AVAILABLE and self._check_redis_available()
        self._local_cache = {}  # Fallback: {key: (value, expiry_timestamp)}
        self._local_cache_lock = False  # Simple lock for demo (not thread-safe, but okay for single process)
        
        if self._use_redis:
            self.redis_client = redis.from_url(self.redis_url)
            # Test connection
            try:
                self.redis_client.ping()
            except Exception as e:
                print(f"Warning: Redis connection failed, falling back to local cache: {e}")
                self._use_redis = False
                self.redis_client = None
        else:
            self.redis_client = None
    
    def _check_redis_available(self) -> bool:
        """Check if Redis is available and we can connect."""
        try:
            # This is a quick check; actual connection is done in __init__
            return True
        except Exception:
            return False
    
    def _make_key(self, key: str) -> str:
        """Prefix key with namespace."""
        return f"{self.namespace}:{key}"
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable if using Redis)
            ttl_seconds: Time to live in seconds. None means no expiration (or default TTL).
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            if self._use_redis:
                # Serialize value to JSON for Redis
                serialized = json.dumps(value, default=str)
                if ttl_seconds is not None:
                    return self.redis_client.setex(self._make_key(key), ttl_seconds, serialized)
                else:
                    # No expiration, use SET
                    return self.redis_client.set(self._make_key(key), serialized)
            else:
                # Local cache with expiry
                expiry = time.time() + ttl_seconds if ttl_seconds is not None else None
                self._local_cache[self._make_key(key)] = (value, expiry)
                return True
        except Exception as e:
            print(f"Error setting cache key {key}: {e}")
            return False
    
    def get(self, key: str) -> Any:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            The cached value, or None if not found or expired.
        """
        try:
            if self._use_redis:
                serialized = self.redis_client.get(self._make_key(key))
                if serialized is None:
                    return None
                return json.loads(serialized)
            else:
                # Local cache
                item = self._local_cache.get(self._make_key(key))
                if item is None:
                    return None
                value, expiry = item
                if expiry is not None and time.time() > expiry:
                    # Expired, delete it
                    del self._local_cache[self._make_key(key)]
                    return None
                return value
        except Exception as e:
            print(f"Error getting cache key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if not found or error.
        """
        try:
            if self._use_redis:
                return bool(self.redis_client.delete(self._make_key(key)))
            else:
                if self._make_key(key) in self._local_cache:
                    del self._local_cache[self._make_key(key)]
                    return True
                return False
        except Exception as e:
            print(f"Error deleting cache key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            if self._use_redis:
                return bool(self.redis_client.exists(self._make_key(key)))
            else:
                item = self._local_cache.get(self._make_key(key))
                if item is None:
                    return False
                _, expiry = item
                return expiry is None or time.time() <= expiry
        except Exception:
            return False
    
    def clear_namespace(self) -> bool:
        """Clear all keys in this namespace."""
        try:
            if self._use_redis:
                # Get all keys in namespace and delete them
                # Note: This can be slow for large namespaces; consider using SCAN in production
                keys = self.redis_client.keys(self._make_key("*"))
                if keys:
                    return bool(self.redis_client.delete(*keys))
                return True
            else:
                # Delete all keys with this namespace
                to_delete = [k for k in self._local_cache.keys() if k.startswith(self._make_key(""))]
                for k in to_delete:
                    del self._local_cache[k]
                return True
        except Exception as e:
            print(f"Error clearing namespace {self.namespace}: {e}")
            return False
    
    def get_ttl(self, key: str) -> Optional[int]:
        """Get time to live for a key in seconds. Returns None if no TTL or key doesn't exist."""
        try:
            if self._use_redis:
                ttl = self.redis_client.ttl(self._make_key(key))
                return ttl if ttl >= 0 else None  # Redis returns -2 if key doesn't exist, -1 if no TTL
            else:
                item = self._local_cache.get(self._make_key(key))
                if item is None:
                    return None
                _, expiry = item
                if expiry is None:
                    return None
                ttl = expiry - time.time()
                return int(ttl) if ttl > 0 else None
        except Exception:
            return None

# Global cache instances (one per namespace)
_cache_instances = {}

def get_cache(namespace: str = "default") -> WhatsAppBusinessCache:
    """Get or create a cache instance for the given namespace."""
    if namespace not in _cache_instances:
        _cache_instances[namespace] = WhatsAppBusinessCache(namespace)
    return _cache_instances[namespace]

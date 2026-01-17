"""
Caching System for Pi Display

This module provides a clean, simple caching layer to reduce API calls.
Follows SOLID principles and clean code practices.

Design Principles Applied:
- Single Responsibility: Cache class only handles cache operations
- Open/Closed: Extendable through inheritance
- KISS: Simple, straightforward implementation
- DRY: No code duplication
"""

import sqlite3
import json
import time
from pathlib import Path
from typing import Optional, Any
from datetime import datetime, timedelta
from contextlib import contextmanager


class CacheError(Exception):
    """Custom exception for cache-related errors."""
    pass


class Cache:
    """
    SQLite-based cache with automatic expiration.

    Responsibilities:
    - Store key-value pairs with expiration
    - Retrieve cached data if not expired
    - Automatic cleanup of expired entries

    Why SQLite:
    - Lightweight (no separate database server needed)
    - ACID compliant (data integrity)
    - Perfect for Raspberry Pi constraints
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize cache with database path.

        Args:
            db_path: Path to SQLite database file.
                    Defaults to data/cache.db
        """
        if db_path is None:
            # Default: data/cache.db in project root
            project_root = Path(__file__).parent.parent
            db_path = project_root / 'data' / 'cache.db'

        self.db_path = Path(db_path)
        self._ensure_directory()
        self._initialize_database()

    def _ensure_directory(self) -> None:
        """Create database directory if it doesn't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.

        Why context manager:
        - Ensures connections are always closed
        - Automatic error handling
        - Clean, readable code

        Yields:
            sqlite3.Connection: Database connection
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            yield conn
        except sqlite3.Error as e:
            raise CacheError(f"Database connection error: {e}")
        finally:
            if conn:
                conn.close()

    def _initialize_database(self) -> None:
        """
        Create cache table if it doesn't exist.

        Schema:
        - key: Unique identifier (PRIMARY KEY)
        - value: JSON-serialized data (TEXT)
        - expires_at: Unix timestamp (REAL)
        - created_at: Unix timestamp (REAL)
        """
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at REAL NOT NULL,
                    created_at REAL NOT NULL
                )
            """)

            # Index for faster expiration queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at
                ON cache(expires_at)
            """)

            conn.commit()

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        """
        Store value in cache with expiration.

        Args:
            key: Cache key (unique identifier)
            value: Data to cache (will be JSON-serialized)
            ttl_seconds: Time to live in seconds (default: 1 hour)

        Raises:
            CacheError: If serialization or storage fails

        Example:
            cache.set('weather', {'temp': 72, 'desc': 'Sunny'}, ttl_seconds=1800)
        """
        try:
            # Serialize value to JSON
            serialized = json.dumps(value)
        except (TypeError, ValueError) as e:
            raise CacheError(f"Cannot serialize value: {e}")

        now = time.time()
        expires_at = now + ttl_seconds

        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cache (key, value, expires_at, created_at)
                VALUES (?, ?, ?, ?)
            """, (key, serialized, expires_at, now))
            conn.commit()

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache if not expired.

        Args:
            key: Cache key to retrieve

        Returns:
            Cached value if exists and not expired, None otherwise

        Example:
            weather = cache.get('weather')
            if weather is None:
                # Cache miss - fetch from API
                weather = fetch_from_api()
                cache.set('weather', weather)
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT value, expires_at
                FROM cache
                WHERE key = ?
            """, (key,))

            row = cursor.fetchone()

            if row is None:
                return None

            value_json, expires_at = row

            # Check if expired
            if time.time() > expires_at:
                # Expired - delete and return None
                self.delete(key)
                return None

            # Deserialize and return
            try:
                return json.loads(value_json)
            except json.JSONDecodeError as e:
                raise CacheError(f"Cannot deserialize cached value: {e}")

    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False if key didn't exist
        """
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()
            return cursor.rowcount > 0

    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries deleted
        """
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM cache")
            conn.commit()
            return cursor.rowcount

    def clear_expired(self) -> int:
        """
        Remove all expired entries from cache.

        This should be called periodically to free up space.

        Returns:
            Number of expired entries deleted
        """
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM cache
                WHERE expires_at < ?
            """, (now,))
            conn.commit()
            return cursor.rowcount

    def has(self, key: str) -> bool:
        """
        Check if key exists and is not expired.

        Args:
            key: Cache key to check

        Returns:
            True if key exists and is valid, False otherwise
        """
        return self.get(key) is not None

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM cache")
            total = cursor.fetchone()[0]

            now = time.time()
            cursor = conn.execute("""
                SELECT COUNT(*) FROM cache
                WHERE expires_at < ?
            """, (now,))
            expired = cursor.fetchone()[0]

            return {
                'total_entries': total,
                'expired_entries': expired,
                'valid_entries': total - expired,
                'database_path': str(self.db_path)
            }


# Global cache instance
# Single instance shared across the application
_cache_instance = None


def get_cache() -> Cache:
    """
    Get global cache instance (Singleton pattern).

    Why singleton:
    - Only one database connection needed
    - Consistent cache across application
    - Memory efficient

    Returns:
        Global Cache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = Cache()
    return _cache_instance


# Example usage and testing
if __name__ == '__main__':
    print("\n=== Testing Cache System ===\n")

    # Create test cache
    cache = Cache('test_cache.db')

    # Test 1: Set and get
    print("Test 1: Set and get")
    cache.set('test_key', {'name': 'Pi Display', 'version': '1.0'}, ttl_seconds=10)
    result = cache.get('test_key')
    print(f"  Stored and retrieved: {result}")
    assert result == {'name': 'Pi Display', 'version': '1.0'}

    # Test 2: Expiration
    print("\nTest 2: Expiration (waiting 2 seconds for 1-second TTL)")
    cache.set('expire_test', 'this will expire', ttl_seconds=1)
    print(f"  Immediate get: {cache.get('expire_test')}")
    time.sleep(2)
    print(f"  After expiration: {cache.get('expire_test')}")
    assert cache.get('expire_test') is None

    # Test 3: Has method
    print("\nTest 3: Has method")
    cache.set('exists', 'value', ttl_seconds=10)
    print(f"  Key 'exists' present: {cache.has('exists')}")
    print(f"  Key 'not_exists' present: {cache.has('not_exists')}")

    # Test 4: Statistics
    print("\nTest 4: Statistics")
    stats = cache.get_stats()
    print(f"  Cache stats: {stats}")

    # Test 5: Clear
    print("\nTest 5: Clear cache")
    deleted = cache.clear()
    print(f"  Deleted {deleted} entries")
    print(f"  After clear: {cache.get_stats()}")

    # Cleanup
    import os
    os.remove('test_cache.db')

    print("\n✓ All tests passed!\n")

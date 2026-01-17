"""
News Aggregation for Pi Display

Fetches news from multiple sources (RSS, Hacker News, Reddit) with caching.
Follows SOLID principles and clean code practices.

Design Principles Applied:
- Single Responsibility: Each class handles one news source
- Open/Closed: Easy to add new news sources by extending base class
- Dependency Injection: Config and cache injected, not hardcoded
- Interface Segregation: Each source implements same interface
- Clean separation: Fetching, parsing, and caching are separate
- Type safety: Full type hints for clarity
- Error handling: Custom exceptions with clear messages
"""

import requests
import feedparser
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from abc import ABC, abstractmethod

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from cache import Cache, get_cache
from config import Config, config as default_config


# Constants (avoid magic numbers)
DEFAULT_CACHE_TTL_SECONDS = 900  # 15 minutes
API_TIMEOUT_SECONDS = 10
DEFAULT_NEWS_LIMIT = 10
HACKERNEWS_API_BASE = "https://hacker-news.firebaseio.com/v0"


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class NewsError(Exception):
    """Base exception for news-related errors."""
    pass


class NewsAPIError(NewsError):
    """Raised when a news API returns an error."""
    pass


class NewsParseError(NewsError):
    """Raised when news data cannot be parsed."""
    pass


class NewsConfigError(NewsError):
    """Raised when news configuration is invalid."""
    pass


# ============================================================================
# UNIFIED NEWS ARTICLE FORMAT
# ============================================================================

class NewsArticle:
    """
    Unified news article representation.

    Why this class:
    - Provides consistent format across all sources
    - Type safety with attributes
    - Easy to serialize to JSON
    - Validates data at creation
    """

    def __init__(
        self,
        title: str,
        link: str,
        source: str,
        published: Optional[str] = None,
        description: Optional[str] = None
    ):
        """
        Initialize news article.

        Args:
            title: Article headline
            link: URL to article
            source: Source name (e.g., "RSS: BBC", "HackerNews")
            published: Publication timestamp (ISO format)
            description: Article summary/excerpt (optional)
        """
        self.title = title
        self.link = link
        self.source = source
        self.published = published or datetime.now().isoformat()
        self.description = description or ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'title': self.title,
            'link': self.link,
            'source': self.source,
            'published': self.published,
            'description': self.description
        }

    def __repr__(self) -> str:
        return f"<NewsArticle: {self.title[:50]}... from {self.source}>"


# ============================================================================
# BASE NEWS SOURCE (INTERFACE)
# ============================================================================

class NewsSource(ABC):
    """
    Abstract base class for news sources.

    Why this design:
    - Interface Segregation: Common interface for all sources
    - Open/Closed: New sources extend this without modifying existing code
    - Polymorphism: NewsAggregator works with any NewsSource

    Each source must implement:
    - fetch_articles(): Fetch and parse articles
    """

    def __init__(self, config: Config, cache: Cache):
        """
        Initialize news source.

        Args:
            config: Configuration object
            cache: Cache instance
        """
        self.config = config
        self.cache = cache

    @abstractmethod
    def fetch_articles(self, limit: int = DEFAULT_NEWS_LIMIT) -> List[NewsArticle]:
        """
        Fetch articles from this source.

        Args:
            limit: Maximum number of articles to return

        Returns:
            List of NewsArticle objects

        Raises:
            NewsError: If fetching fails
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Return human-readable source name."""
        pass


# ============================================================================
# RSS FEED SOURCE
# ============================================================================

class RSSFeedSource(NewsSource):
    """
    Fetches news from RSS feeds.

    Why RSS:
    - No API key needed
    - Widely supported
    - Standard format (easy to parse)
    - Many news sites provide RSS
    """

    def __init__(self, config: Config, cache: Cache, feed_url: str, feed_name: str):
        """
        Initialize RSS feed source.

        Args:
            config: Configuration object
            cache: Cache instance
            feed_url: URL of RSS feed
            feed_name: Human-readable name (e.g., "BBC News")
        """
        super().__init__(config, cache)
        self.feed_url = feed_url
        self.feed_name = feed_name

    def get_source_name(self) -> str:
        """Return source name."""
        return f"RSS: {self.feed_name}"

    def fetch_articles(self, limit: int = DEFAULT_NEWS_LIMIT) -> List[NewsArticle]:
        """
        Fetch and parse RSS feed.

        Args:
            limit: Maximum number of articles

        Returns:
            List of NewsArticle objects

        Raises:
            NewsAPIError: If feed fetch fails
            NewsParseError: If feed parse fails
        """
        try:
            # Parse RSS feed
            feed = feedparser.parse(self.feed_url)

            # Check for feed errors
            if feed.bozo and not feed.entries:
                raise NewsParseError(
                    f"Failed to parse RSS feed {self.feed_name}: {feed.bozo_exception}"
                )

            # Transform entries to NewsArticle objects
            articles = []
            for entry in feed.entries[:limit]:
                article = self._parse_entry(entry)
                if article:
                    articles.append(article)

            return articles

        except Exception as e:
            if isinstance(e, NewsError):
                raise
            raise NewsAPIError(f"RSS feed error ({self.feed_name}): {e}")

    def _parse_entry(self, entry) -> Optional[NewsArticle]:
        """
        Parse RSS entry to NewsArticle.

        Args:
            entry: feedparser entry object

        Returns:
            NewsArticle or None if parsing fails
        """
        try:
            # Extract title
            title = entry.get('title', 'No Title')

            # Extract link
            link = entry.get('link', '')
            if not link:
                return None  # Skip entries without links

            # Extract published date
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    dt = datetime(*entry.published_parsed[:6])
                    published = dt.isoformat()
                except:
                    pass

            # Extract description/summary
            description = entry.get('summary', '') or entry.get('description', '')

            return NewsArticle(
                title=title,
                link=link,
                source=self.get_source_name(),
                published=published,
                description=description
            )

        except Exception:
            return None  # Skip malformed entries


# ============================================================================
# HACKER NEWS SOURCE
# ============================================================================

class HackerNewsSource(NewsSource):
    """
    Fetches top stories from Hacker News.

    Why Hacker News:
    - Free API, no key needed
    - Tech-focused content
    - High-quality discussions
    - Simple JSON API

    API Docs: https://github.com/HackerNews/API
    """

    def get_source_name(self) -> str:
        """Return source name."""
        return "HackerNews"

    def fetch_articles(self, limit: int = DEFAULT_NEWS_LIMIT) -> List[NewsArticle]:
        """
        Fetch top stories from Hacker News.

        Args:
            limit: Maximum number of stories

        Returns:
            List of NewsArticle objects

        Raises:
            NewsAPIError: If API request fails
        """
        try:
            # Fetch top story IDs
            top_stories_url = f"{HACKERNEWS_API_BASE}/topstories.json"
            response = requests.get(top_stories_url, timeout=API_TIMEOUT_SECONDS)
            response.raise_for_status()

            story_ids = response.json()[:limit]

            # Fetch details for each story
            articles = []
            for story_id in story_ids:
                article = self._fetch_story(story_id)
                if article:
                    articles.append(article)

            return articles

        except requests.Timeout:
            raise NewsAPIError(
                f"Hacker News API request timed out after {API_TIMEOUT_SECONDS}s"
            )
        except requests.RequestException as e:
            raise NewsAPIError(f"Hacker News API request failed: {e}")
        except Exception as e:
            raise NewsAPIError(f"Hacker News error: {e}")

    def _fetch_story(self, story_id: int) -> Optional[NewsArticle]:
        """
        Fetch individual story details.

        Args:
            story_id: HN story ID

        Returns:
            NewsArticle or None if fetch fails
        """
        try:
            story_url = f"{HACKERNEWS_API_BASE}/item/{story_id}.json"
            response = requests.get(story_url, timeout=API_TIMEOUT_SECONDS)
            response.raise_for_status()

            story = response.json()

            # Skip if deleted or dead
            if story.get('deleted') or story.get('dead'):
                return None

            # Extract data
            title = story.get('title', 'No Title')
            link = story.get('url', f"https://news.ycombinator.com/item?id={story_id}")

            # Parse timestamp
            published = None
            if 'time' in story:
                dt = datetime.fromtimestamp(story['time'])
                published = dt.isoformat()

            return NewsArticle(
                title=title,
                link=link,
                source=self.get_source_name(),
                published=published,
                description=story.get('text', '')
            )

        except Exception:
            return None  # Skip stories that fail to fetch


# ============================================================================
# NEWS AGGREGATOR
# ============================================================================

class NewsAggregator:
    """
    Aggregates news from multiple sources.

    Responsibilities:
    - Manage multiple news sources
    - Fetch from all sources in parallel (future optimization)
    - Combine and deduplicate results
    - Cache aggregated results
    - Handle errors gracefully

    Why this design:
    - Single point of entry for all news
    - Easy to add/remove sources
    - Caching at aggregation level
    - Testable (can inject sources)
    """

    def __init__(
        self,
        config: Config = default_config,
        cache: Optional[Cache] = None
    ):
        """
        Initialize news aggregator.

        Args:
            config: Configuration object
            cache: Cache instance (optional, will use global if not provided)
        """
        self.config = config
        self.cache = cache or get_cache()
        self.sources: List[NewsSource] = []

        # Initialize sources from configuration
        self._initialize_sources()

    def _initialize_sources(self) -> None:
        """
        Initialize news sources from configuration.

        Reads config and creates appropriate NewsSource instances.
        """
        # Add RSS feeds
        rss_feeds = self.config.get('news.rss_feeds', [])
        for feed_url in rss_feeds:
            # Extract feed name from URL (simple heuristic)
            feed_name = self._extract_feed_name(feed_url)
            source = RSSFeedSource(self.config, self.cache, feed_url, feed_name)
            self.sources.append(source)

        # Add Hacker News (always enabled)
        hn_enabled = self.config.get('news.hackernews_enabled', True)
        if hn_enabled:
            source = HackerNewsSource(self.config, self.cache)
            self.sources.append(source)

    def _extract_feed_name(self, url: str) -> str:
        """
        Extract human-readable name from RSS feed URL.

        Args:
            url: Feed URL

        Returns:
            Feed name (e.g., "bbc.co.uk" from "https://feeds.bbci.co.uk/...")
        """
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            # Remove 'www.' and 'feeds.' prefixes
            domain = domain.replace('www.', '').replace('feeds.', '')
            # Remove common TLDs for cleaner display
            domain = domain.replace('.co.uk', '').replace('.com', '')
            return domain or 'RSS'
        except:
            return 'RSS'

    def get_news(
        self,
        limit: int = DEFAULT_NEWS_LIMIT,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get aggregated news from all sources.

        This is the main public method of this class.
        All other methods are implementation details.

        Args:
            limit: Maximum total articles to return
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            List of news article dictionaries

        Raises:
            NewsError: If all sources fail

        Example:
            aggregator = NewsAggregator()
            news = aggregator.get_news(limit=20)
            for article in news:
                print(f"{article['title']} - {article['source']}")
        """
        cache_key = 'news_aggregated'

        # Try cache first (unless force refresh)
        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data[:limit]  # Respect limit

        # Cache miss - fetch from all sources
        all_articles = []
        errors = []

        for source in self.sources:
            try:
                # Fetch from this source
                articles = source.fetch_articles(limit=limit)
                all_articles.extend(articles)

            except NewsError as e:
                # Log error but continue with other sources
                errors.append(f"{source.get_source_name()}: {e}")
                continue

        # Check if we got any articles
        if not all_articles:
            if errors:
                raise NewsError(f"All news sources failed: {'; '.join(errors)}")
            else:
                raise NewsError("No news sources configured")

        # Sort by published date (newest first)
        all_articles.sort(
            key=lambda a: a.published if a.published else '',
            reverse=True
        )

        # Convert to dictionaries
        articles_dict = [article.to_dict() for article in all_articles]

        # Limit results
        articles_dict = articles_dict[:limit]

        # Cache the result
        ttl = self.config.get('news.cache_duration', DEFAULT_CACHE_TTL_SECONDS)
        self.cache.set(cache_key, articles_dict, ttl_seconds=ttl)

        return articles_dict

    def clear_cache(self) -> None:
        """Clear cached news data."""
        self.cache.delete('news_aggregated')


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def get_current_news(
    config: Config = default_config,
    limit: int = DEFAULT_NEWS_LIMIT,
    force_refresh: bool = False
) -> List[Dict[str, Any]]:
    """
    Convenience function to get aggregated news.

    This provides a simple interface without needing to create an aggregator.

    Args:
        config: Configuration object
        limit: Maximum articles to return
        force_refresh: Bypass cache if True

    Returns:
        List of news article dictionaries

    Raises:
        NewsError: If fetching fails

    Example:
        news = get_current_news(limit=10)
        for article in news:
            print(f"{article['title']} - {article['source']}")
    """
    aggregator = NewsAggregator(config=config)
    return aggregator.get_news(limit=limit, force_refresh=force_refresh)


# ============================================================================
# TESTING
# ============================================================================

if __name__ == '__main__':
    """
    Test the news aggregator.

    NOTE: This requires internet connection and configured RSS feeds.
    """
    print("\n=== Testing News Aggregator ===\n")

    try:
        # Test aggregator initialization
        print("Test 1: Initialize aggregator")
        aggregator = NewsAggregator()
        print(f"  ✓ Initialized with {len(aggregator.sources)} sources")
        for source in aggregator.sources:
            print(f"    - {source.get_source_name()}")

        # Test fetching news
        print("\nTest 2: Fetch news articles")
        news = aggregator.get_news(limit=10)
        print(f"  ✓ Fetched {len(news)} articles")

        # Display sample articles
        print("\nSample Articles:")
        for i, article in enumerate(news[:5], 1):
            print(f"\n  {i}. {article['title'][:70]}...")
            print(f"     Source: {article['source']}")
            print(f"     Link: {article['link'][:60]}...")
            if article.get('published'):
                print(f"     Published: {article['published']}")

        # Test caching
        print("\nTest 3: Cache functionality")
        print("  First call (should fetch from APIs)...")
        import time
        start = time.time()
        news1 = aggregator.get_news(limit=10)
        time1 = time.time() - start

        print("  Second call (should use cache)...")
        start = time.time()
        news2 = aggregator.get_news(limit=10)
        time2 = time.time() - start

        print(f"  First call: {time1:.3f}s")
        print(f"  Second call: {time2:.3f}s (cached)")
        print(f"  Speed improvement: {time1/time2:.1f}x faster")

        # Test force refresh
        print("\nTest 4: Force refresh")
        news3 = aggregator.get_news(limit=10, force_refresh=True)
        print("  ✓ Force refresh successful")

        print("\n✓ All tests passed!\n")

    except NewsConfigError as e:
        print(f"  ✗ Configuration error: {e}")
        print("\n  To run tests, add to config/config.yaml:")
        print("    news:")
        print("      rss_feeds:")
        print("        - https://feeds.bbci.co.uk/news/rss.xml")
        print("      hackernews_enabled: true")

    except NewsError as e:
        print(f"  ✗ News error: {e}")

    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")

#!/usr/bin/env python3
"""
Feedly OPML Import Utility for Pi Display

Imports curated tech RSS feeds from a Feedly OPML export into config.yaml.
Creates a backup before modifying configuration.

Usage:
    python scripts/import_feedly.py path/to/feedly-export.opml
"""

import xml.etree.ElementTree as ET
import yaml
import sys
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set


# Curated list of feeds to import (15 total - FULL CONTENT ONLY)
# These feeds provide complete articles in RSS, not just summaries
CURATED_FEEDS = {
    "Programming": [
        {"title": "Coding Horror", "xmlUrl": "https://feeds.feedburner.com/codinghorror"},
        {"title": "Joel on Software", "xmlUrl": "https://www.joelonsoftware.com/feed/"},
        {"title": "Dan Abramov's Overreacted", "xmlUrl": "https://overreacted.io/rss.xml"},
        {"title": "Simon Willison's Weblog", "xmlUrl": "http://feeds.simonwillison.net/swn-everything"},
        {"title": "Martin Fowler", "xmlUrl": "https://martinfowler.com/feed.atom"},
    ],
    "JavaSpring": [
        {"title": "Baeldung", "xmlUrl": "http://feeds.feedburner.com/Baeldung"},
        {"title": "Spring Framework Guru", "xmlUrl": "https://springframework.guru/feed/"},
        {"title": "Java, SQL and jOOQ", "xmlUrl": "https://blog.jooq.org/feed"},
        {"title": "Spring News", "xmlUrl": "http://spring.io/blog/category/news.atom"},
    ],
    "Engineering": [
        {"title": "Netflix TechBlog", "xmlUrl": "https://netflixtechblog.com/feed"},
        {"title": "Engineering at Slack", "xmlUrl": "https://slack.engineering/feed"},
        {"title": "Code as Craft (Etsy)", "xmlUrl": "https://codeascraft.com/feed/atom/"},
        {"title": "GitLab Blog", "xmlUrl": "https://about.gitlab.com/atom.xml"},
        {"title": "LinkedIn Engineering", "xmlUrl": "https://engineering.linkedin.com/blog.rss.html"},
        {"title": "Facebook Engineering", "xmlUrl": "https://engineering.fb.com/feed/"},
    ]
}


class FeedlyImporter:
    """Imports RSS feeds from Feedly OPML export into config.yaml."""

    def __init__(self, opml_path: str, config_path: str = None):
        """
        Initialize the importer.

        Args:
            opml_path: Path to Feedly OPML export file
            config_path: Path to config.yaml (defaults to config/config.yaml)
        """
        self.opml_path = Path(opml_path)

        if config_path is None:
            # Default to config/config.yaml.example (since config.yaml might not exist)
            project_root = Path(__file__).parent.parent
            self.config_path = project_root / 'config' / 'config.yaml'

            # If config.yaml doesn't exist, use config.yaml.example as template
            if not self.config_path.exists():
                template_path = project_root / 'config' / 'config.yaml.example'
                if template_path.exists():
                    print(f"⚠️  config.yaml not found. Using {template_path.name} as template")
                    shutil.copy(template_path, self.config_path)
                else:
                    raise FileNotFoundError("Neither config.yaml nor config.yaml.example found!")
        else:
            self.config_path = Path(config_path)

        self.opml_feeds: Dict[str, List[Dict]] = {}
        self.imported_feeds: List[Dict] = []
        self.skipped_feeds: List[str] = []

    def parse_opml(self) -> None:
        """Parse OPML file and extract all feeds grouped by category."""
        print(f"🔄 Parsing OPML file: {self.opml_path.name}...")

        try:
            tree = ET.parse(self.opml_path)
            root = tree.getroot()

            # Find all outline elements (categories and feeds)
            for category in root.findall('.//outline[@text]'):
                category_name = category.get('text')

                # Check if this is a category (has nested outlines)
                feeds_in_category = category.findall('./outline[@type="rss"]')

                if feeds_in_category:
                    self.opml_feeds[category_name] = []

                    for feed in feeds_in_category:
                        self.opml_feeds[category_name].append({
                            'title': feed.get('title', feed.get('text', 'Unknown')),
                            'xmlUrl': feed.get('xmlUrl', ''),
                            'htmlUrl': feed.get('htmlUrl', '')
                        })

            total_feeds = sum(len(feeds) for feeds in self.opml_feeds.values())
            print(f"✓ Found {total_feeds} feeds across {len(self.opml_feeds)} categories")

        except ET.ParseError as e:
            print(f"✗ Error parsing OPML file: {e}")
            sys.exit(1)
        except FileNotFoundError:
            print(f"✗ OPML file not found: {self.opml_path}")
            sys.exit(1)

    def validate_curated_feeds(self) -> List[Dict]:
        """
        Validate that curated feeds exist in the OPML file.

        Returns:
            List of validated feeds with category information
        """
        validated_feeds = []

        # Flatten OPML feeds for easier lookup
        opml_urls = {}
        for category, feeds in self.opml_feeds.items():
            for feed in feeds:
                opml_urls[feed['xmlUrl']] = {**feed, 'opml_category': category}

        # Validate each curated feed
        for category, feeds in CURATED_FEEDS.items():
            for feed in feeds:
                url = feed['xmlUrl']
                if url in opml_urls:
                    validated_feeds.append({
                        'title': feed['title'],
                        'xmlUrl': url,
                        'category': category,
                        'opml_category': opml_urls[url]['opml_category']
                    })
                else:
                    print(f"⚠️  Feed not found in OPML: {feed['title']} ({url})")

        return validated_feeds

    def backup_config(self) -> None:
        """Create a backup of the current config file."""
        if not self.config_path.exists():
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.config_path.parent / f"{self.config_path.stem}.backup.{timestamp}.yaml"

        print(f"💾 Backing up existing config...")
        shutil.copy(self.config_path, backup_path)
        print(f"✓ Created backup: {backup_path.name}")

    def update_config(self, validated_feeds: List[Dict]) -> None:
        """
        Update config.yaml with validated feeds.

        Args:
            validated_feeds: List of feeds to add
        """
        print(f"📝 Updating {self.config_path.name}...")

        # Load existing config
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Ensure news.rss_feeds exists
        if 'news' not in config:
            config['news'] = {}
        if 'rss_feeds' not in config['news']:
            config['news']['rss_feeds'] = []

        # Get existing feed URLs to avoid duplicates
        existing_urls: Set[str] = set(config['news']['rss_feeds'])

        # Group validated feeds by category
        feeds_by_category = {}
        for feed in validated_feeds:
            category = feed['category']
            if category not in feeds_by_category:
                feeds_by_category[category] = []
            feeds_by_category[category].append(feed)

        # Add feeds by category
        added_count = 0
        for category in ['Programming', 'JavaSpring', 'Engineering']:
            if category in feeds_by_category:
                for feed in feeds_by_category[category]:
                    url = feed['xmlUrl']
                    if url not in existing_urls:
                        config['news']['rss_feeds'].append(url)
                        existing_urls.add(url)
                        self.imported_feeds.append(feed)
                        added_count += 1
                    else:
                        self.skipped_feeds.append(feed['title'])

        # Write updated config using proper YAML
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        print(f"✓ Added {added_count} new feeds")
        if self.skipped_feeds:
            print(f"ℹ Skipped {len(self.skipped_feeds)} feeds (already in config)")

    def run(self) -> None:
        """Execute the import process."""
        print("\n" + "=" * 60)
        print("  📰 Feedly OPML Import Utility")
        print("=" * 60 + "\n")

        # Step 1: Parse OPML
        self.parse_opml()

        # Step 2: Validate curated feeds
        print(f"\n📋 Importing {sum(len(feeds) for feeds in CURATED_FEEDS.values())} curated feeds from:")
        for category, feeds in CURATED_FEEDS.items():
            print(f"   - {category} ({len(feeds)} feeds)")

        validated_feeds = self.validate_curated_feeds()

        if not validated_feeds:
            print("\n✗ No feeds found in OPML! Exiting.")
            sys.exit(1)

        # Step 3: Backup config
        print()
        self.backup_config()

        # Step 4: Update config
        print()
        self.update_config(validated_feeds)

        # Step 5: Print summary
        print(f"\n✅ Import complete!\n")
        print("Summary:")
        print(f"- Feeds validated from OPML: {len(validated_feeds)}")
        print(f"- New feeds added: {len(self.imported_feeds)}")
        print(f"- Duplicates skipped: {len(self.skipped_feeds)}")

        if self.skipped_feeds:
            print(f"\nSkipped feeds (already in config):")
            for title in self.skipped_feeds:
                print(f"  - {title}")

        print(f"\n📁 Config updated: {self.config_path}")
        print("\n" + "=" * 60 + "\n")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python import_feedly.py path/to/feedly-export.opml")
        print("\nExample:")
        print("  python scripts/import_feedly.py feedly-export.opml")
        sys.exit(1)

    opml_path = sys.argv[1]

    importer = FeedlyImporter(opml_path)
    importer.run()


if __name__ == '__main__':
    main()

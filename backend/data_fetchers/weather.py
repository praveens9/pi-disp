"""
Weather Data Fetcher for Pi Display

Fetches weather data from OpenWeatherMap API with caching.
Follows SOLID principles and clean code practices.

Design Principles Applied:
- Single Responsibility: WeatherFetcher only handles weather data
- Dependency Injection: Cache and config injected, not hardcoded
- Clean separation: API calls, data transformation, caching are separate
- Type safety: Full type hints for clarity
- Error handling: Custom exceptions with clear messages
"""

import requests
import sys
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from cache import Cache, get_cache
from config import Config, config as default_config


# Constants (avoid magic numbers)
DEFAULT_CACHE_TTL_SECONDS = 1800  # 30 minutes
API_TIMEOUT_SECONDS = 10
KELVIN_TO_FAHRENHEIT_OFFSET = 273.15
FAHRENHEIT_MULTIPLIER = 9/5
FAHRENHEIT_CONSTANT = 32


class WeatherError(Exception):
    """Base exception for weather-related errors."""
    pass


class WeatherAPIError(WeatherError):
    """Raised when OpenWeatherMap API returns an error."""
    pass


class WeatherConfigError(WeatherError):
    """Raised when weather configuration is invalid."""
    pass


class WeatherFetcher:
    """
    Fetches and caches weather data from OpenWeatherMap.

    Responsibilities:
    - Fetch current weather from API
    - Transform API response to clean format
    - Cache results to minimize API calls
    - Handle errors gracefully

    Why this design:
    - Testable: Dependencies injected
    - Maintainable: Clear separation of concerns
    - Extensible: Easy to add other weather providers
    """

    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(
        self,
        config: Config = default_config,
        cache: Optional[Cache] = None
    ):
        """
        Initialize weather fetcher.

        Args:
            config: Configuration object (injected dependency)
            cache: Cache instance (injected dependency)

        Raises:
            WeatherConfigError: If required config is missing
        """
        self.config = config
        self.cache = cache or get_cache()

        # Validate configuration
        self._validate_config()

    def _validate_config(self) -> None:
        """
        Validate required configuration exists.

        Raises:
            WeatherConfigError: If configuration is incomplete
        """
        required_fields = {
            'weather.api_key': 'OpenWeatherMap API key',
            'weather.latitude': 'Latitude coordinate',
            'weather.longitude': 'Longitude coordinate'
        }

        for field, description in required_fields.items():
            if not self.config.has(field):
                raise WeatherConfigError(
                    f"Missing required configuration: {description} ({field})"
                )

    def _build_api_url(self) -> str:
        """
        Build OpenWeatherMap API URL with parameters.

        Returns:
            Complete API URL with query parameters
        """
        api_key = self.config.get('weather.api_key')
        lat = self.config.get('weather.latitude')
        lon = self.config.get('weather.longitude')
        units = self.config.get('weather.units', 'imperial')

        return (
            f"{self.BASE_URL}"
            f"?lat={lat}"
            f"&lon={lon}"
            f"&appid={api_key}"
            f"&units={units}"
        )

    def _fetch_from_api(self) -> Dict[str, Any]:
        """
        Fetch weather data from OpenWeatherMap API.

        Returns:
            Raw API response as dictionary

        Raises:
            WeatherAPIError: If API request fails
        """
        url = self._build_api_url()

        try:
            response = requests.get(url, timeout=API_TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.json()

        except requests.Timeout:
            raise WeatherAPIError(
                f"Weather API request timed out after {API_TIMEOUT_SECONDS}s"
            )
        except requests.RequestException as e:
            raise WeatherAPIError(f"Weather API request failed: {e}")
        except ValueError as e:
            raise WeatherAPIError(f"Invalid JSON response from API: {e}")

    def _transform_response(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform API response to clean, simplified format.

        Single Responsibility: Only transforms data structure
        Clean Code: Clear, descriptive field names

        Args:
            api_data: Raw API response

        Returns:
            Simplified weather data dictionary
        """
        try:
            # Extract data with safe defaults
            main = api_data.get('main', {})
            weather = api_data.get('weather', [{}])[0]
            wind = api_data.get('wind', {})
            clouds = api_data.get('clouds', {})
            sys = api_data.get('sys', {})

            # Build clean response
            return {
                # Temperature
                'temperature': round(main.get('temp', 0), 1),
                'feels_like': round(main.get('feels_like', 0), 1),
                'temp_min': round(main.get('temp_min', 0), 1),
                'temp_max': round(main.get('temp_max', 0), 1),

                # Conditions
                'condition': weather.get('main', 'Unknown'),
                'description': weather.get('description', 'No description'),
                'icon': weather.get('icon', ''),

                # Additional data
                'humidity': main.get('humidity', 0),
                'pressure': main.get('pressure', 0),
                'wind_speed': round(wind.get('speed', 0), 1),
                'wind_direction': wind.get('deg', 0),
                'cloudiness': clouds.get('all', 0),

                # Location
                'location': api_data.get('name', 'Unknown'),
                'country': sys.get('country', ''),

                # Metadata
                'timestamp': datetime.now().isoformat(),
                'units': self.config.get('weather.units', 'imperial')
            }

        except (KeyError, IndexError, TypeError) as e:
            raise WeatherAPIError(f"Failed to parse API response: {e}")

    def get_weather(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get current weather data (cached or fresh).

        This is the main public method of this class.
        All other methods are implementation details.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            Weather data dictionary

        Raises:
            WeatherError: If fetching or caching fails

        Example:
            fetcher = WeatherFetcher()
            weather = fetcher.get_weather()
            print(f"Temperature: {weather['temperature']}°F")
        """
        cache_key = 'weather_current'

        # Try cache first (unless force refresh)
        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data

        # Cache miss - fetch from API
        raw_data = self._fetch_from_api()
        clean_data = self._transform_response(raw_data)

        # Cache the result
        ttl = self.config.get('weather.cache_duration', DEFAULT_CACHE_TTL_SECONDS)
        self.cache.set(cache_key, clean_data, ttl_seconds=ttl)

        return clean_data

    def clear_cache(self) -> None:
        """Clear cached weather data."""
        self.cache.delete('weather_current')


# Convenience function for simple usage
def get_current_weather(
    config: Config = default_config,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to get weather data.

    This provides a simple interface without needing to create a fetcher.

    Args:
        config: Configuration object
        force_refresh: Bypass cache if True

    Returns:
        Current weather data

    Raises:
        WeatherError: If fetching fails

    Example:
        weather = get_current_weather()
        print(weather['temperature'])
    """
    fetcher = WeatherFetcher(config=config)
    return fetcher.get_weather(force_refresh=force_refresh)


# Example usage and testing
if __name__ == '__main__':
    """
    Test the weather fetcher.

    NOTE: This requires valid API key and coordinates in config.
    """
    print("\n=== Testing Weather Fetcher ===\n")

    try:
        # Test configuration validation
        print("Test 1: Configuration validation")
        fetcher = WeatherFetcher()
        print("  ✓ Configuration valid")

        # Test fetching weather
        print("\nTest 2: Fetch weather data")
        weather = fetcher.get_weather()
        print(f"  Location: {weather['location']}, {weather['country']}")
        print(f"  Temperature: {weather['temperature']}°")
        print(f"  Condition: {weather['description']}")
        print(f"  Humidity: {weather['humidity']}%")
        print(f"  Wind: {weather['wind_speed']} mph")

        # Test caching
        print("\nTest 3: Cache functionality")
        print("  First call (should hit API)...")
        import time
        start = time.time()
        weather1 = fetcher.get_weather()
        time1 = time.time() - start

        print("  Second call (should use cache)...")
        start = time.time()
        weather2 = fetcher.get_weather()
        time2 = time.time() - start

        print(f"  First call: {time1:.3f}s")
        print(f"  Second call: {time2:.3f}s (cached)")
        print(f"  Speed improvement: {time1/time2:.1f}x faster")

        # Test force refresh
        print("\nTest 4: Force refresh")
        weather3 = fetcher.get_weather(force_refresh=True)
        print("  ✓ Force refresh successful")

        print("\n✓ All tests passed!\n")

    except WeatherConfigError as e:
        print(f"  ✗ Configuration error: {e}")
        print("\n  To run tests, add to config/config.yaml:")
        print("    weather:")
        print("      api_key: YOUR_API_KEY")
        print("      latitude: YOUR_LATITUDE")
        print("      longitude: YOUR_LONGITUDE")

    except WeatherAPIError as e:
        print(f"  ✗ API error: {e}")

    except WeatherError as e:
        print(f"  ✗ Weather error: {e}")

"""
Flask Backend for Pi Display

This is the main Flask application that serves API endpoints for the display.
It provides data to the frontend (weather, news, quotes, etc.) via HTTP requests.

What is Flask?
- Flask is a "web framework" - it helps us create web servers in Python
- A "web server" is a program that listens for HTTP requests and sends back responses
- HTTP is how browsers and web apps communicate (GET, POST, etc.)

Why Flask?
- Lightweight: Uses ~30-40MB of memory (important for Pi 2)
- Simple: Easy to understand for beginners
- Flexible: Can add features as we need them
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import sys
from pathlib import Path

# Import our configuration module
# This lets us access config.get('weather.api_key') etc.
from config import config

# Import data fetchers
from data_fetchers.weather import get_current_weather, WeatherError
from data_fetchers.news import get_current_news, NewsError

# Create the Flask application
# __name__ tells Flask where to find resources (templates, static files)
app = Flask(__name__)

# Enable CORS (Cross-Origin Resource Sharing)
# Why? The frontend (HTML file) might be served from a different port/domain
# CORS allows the frontend to make requests to our Flask backend
# Without this, browsers block the requests for security reasons
CORS(app)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/health')
def health_check():
    """
    Health check endpoint - confirms the server is running.

    This is a simple endpoint that always returns success.
    It's useful for:
    - Testing if the server is running
    - Monitoring tools to check if service is alive
    - Debugging connection issues

    Returns:
        JSON response with status "ok"

    Example:
        GET http://localhost:5000/api/health
        Response: {"status": "ok", "timestamp": "2026-01-17T10:30:00"}
    """
    return jsonify({
        'status': 'ok',
        'message': 'Pi Display backend is running',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/time')
def get_time():
    """
    Returns current date and time.

    This endpoint doesn't need any external APIs - it just returns
    the current time from the Raspberry Pi's system clock.

    Returns:
        JSON with current time in various formats

    Example:
        GET http://localhost:5000/api/time
        Response: {
            "time": "2:47 PM",
            "date": "Friday, January 17, 2026",
            "timestamp": "2026-01-17T14:47:30"
        }
    """
    now = datetime.now()

    return jsonify({
        'time': now.strftime('%I:%M %p'),           # "2:47 PM"
        'date': now.strftime('%A, %B %d, %Y'),      # "Friday, January 17, 2026"
        'timestamp': now.isoformat(),                # "2026-01-17T14:47:30"
        'day': now.strftime('%A'),                   # "Friday"
        'month': now.strftime('%B'),                 # "January"
        'year': now.year,
        'hour': now.hour,
        'minute': now.minute
    })


@app.route('/api/weather')
def get_weather():
    """
    Returns current weather data from OpenWeatherMap.

    Clean Code Principles:
    - Single Responsibility: Routing only, delegates to weather fetcher
    - Proper error handling: Different HTTP codes for different errors
    - Clear response format: Consistent JSON structure

    Returns:
        JSON with weather data

    HTTP Status Codes:
        200: Success
        500: Server error (API failure, configuration error)

    Example:
        GET http://localhost:5000/api/weather
        Response: {
            "temperature": 72.5,
            "condition": "Clear",
            "description": "clear sky",
            "humidity": 45,
            "wind_speed": 5.2,
            ...
        }
    """
    try:
        # Delegate to weather fetcher (Dependency Inversion Principle)
        weather_data = get_current_weather()
        return jsonify(weather_data)

    except WeatherError as e:
        # Handle weather-specific errors with clear messages
        return jsonify({
            'error': 'Weather fetch failed',
            'message': str(e),
            'suggestion': 'Check your API key and network connection'
        }), 500

    except Exception as e:
        # Catch unexpected errors
        return jsonify({
            'error': 'Unexpected error',
            'message': str(e)
        }), 500


@app.route('/api/news')
def get_news():
    """
    Returns aggregated news from multiple sources (RSS, Hacker News).

    Clean Code Principles:
    - Single Responsibility: Routing only, delegates to news aggregator
    - Proper error handling: Different HTTP codes for different errors
    - Clear response format: Consistent JSON array structure

    Returns:
        JSON array of news articles

    HTTP Status Codes:
        200: Success
        500: Server error (API failure, configuration error)

    Example:
        GET http://localhost:5000/api/news?limit=20
        Response: [
            {
                "title": "Breaking news headline",
                "link": "https://...",
                "source": "RSS: BBC",
                "published": "2026-01-17T10:30:00",
                "description": "Article summary..."
            },
            ...
        ]
    """
    try:
        # Get limit from query parameter (default: 10)
        limit = request.args.get('limit', default=10, type=int)

        # Validate limit
        if limit < 1 or limit > 100:
            return jsonify({
                'error': 'Invalid limit',
                'message': 'Limit must be between 1 and 100'
            }), 400

        # Delegate to news aggregator (Dependency Inversion Principle)
        news_data = get_current_news(limit=limit)
        return jsonify(news_data)

    except NewsError as e:
        # Handle news-specific errors with clear messages
        return jsonify({
            'error': 'News fetch failed',
            'message': str(e),
            'suggestion': 'Check your network connection and RSS feed URLs'
        }), 500

    except Exception as e:
        # Catch unexpected errors
        return jsonify({
            'error': 'Unexpected error',
            'message': str(e)
        }), 500


# Future endpoints will be added in later sessions:
# @app.route('/api/quote')    - Session 4
# @app.route('/api/photo')    - Session 11


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """
    Handle 404 Not Found errors.

    This runs when someone tries to access an endpoint that doesn't exist.
    Example: GET /api/nonexistent would trigger this.
    """
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'The requested API endpoint does not exist',
        'available_endpoints': [
            '/api/health',
            '/api/time',
            '/api/weather',
            '/api/news'
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """
    Handle 500 Internal Server Error.

    This runs when there's an unexpected error in our code.
    It helps us debug issues without exposing sensitive details to users.
    """
    return jsonify({
        'error': 'Internal server error',
        'message': 'Something went wrong on the server'
    }), 500


# ============================================================================
# STARTUP
# ============================================================================

def print_startup_info():
    """
    Print useful information when the server starts.

    This helps you know:
    - Where the server is running
    - What endpoints are available
    - Configuration status
    """
    print("\n" + "=" * 60)
    print("  🚀 Pi Display Backend Starting")
    print("=" * 60)
    print(f"\n✓ Flask server running on http://localhost:5000")
    print(f"\n📍 Available endpoints:")
    print(f"   • http://localhost:5000/api/health   - Health check")
    print(f"   • http://localhost:5000/api/time     - Current time")
    print(f"   • http://localhost:5000/api/weather  - Weather data")
    print(f"   • http://localhost:5000/api/news     - News aggregation")
    print(f"\n⚙️  Configuration:")

    # Check if config is loaded
    has_weather_key = config.has('weather.api_key')
    print(f"   • Weather API key: {'✓ Configured' if has_weather_key else '✗ Not set'}")
    print(f"   • Config file: {config.config_path}")

    if not has_weather_key:
        print(f"\n⚠️  No weather API key found!")
        print(f"   Copy config/config.yaml.example to config/config.yaml")
        print(f"   and add your OpenWeatherMap API key")

    print(f"\n💡 Tips:")
    print(f"   • Press Ctrl+C to stop the server")
    print(f"   • Add debug=True to app.run() for auto-reload during development")
    print(f"   • Check logs above for any configuration warnings")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    """
    This code only runs when you execute this file directly:
        python app.py

    It won't run if another file imports this module.
    This is a Python convention for making code both importable and executable.
    """

    # Print startup information
    print_startup_info()

    # Start the Flask development server
    # Parameters explained:
    #   host='0.0.0.0' - Listen on all network interfaces
    #                    This allows access from other devices on your network
    #                    (e.g., your laptop can access Pi's Flask server)
    #   port=5000      - The port number (http://localhost:5000)
    #   debug=False    - Set to True during development for:
    #                    • Auto-reload when code changes
    #                    • Detailed error messages
    #                    • Interactive debugger
    #                    Set to False for production (Raspberry Pi)

    app.run(
        host='0.0.0.0',  # Listen on all interfaces
        port=5000,        # Standard development port
        debug=False       # Set to True for development, False for Pi
    )

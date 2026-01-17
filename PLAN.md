# Raspberry Pi Information Display - Implementation Plan

## Project Overview
Build a lightweight information display system for Raspberry Pi 2 that shows weather, news, photos, quotes, and time on a 22" LCD monitor. Future extension: Google Speaker voice assistant integration with LLM-powered Q&A displayed on screen.

**User Experience Level**: Beginner - code will include detailed explanations and comments

---

## Quick Start (When Ready to Begin)

**To start Session 1, simply say**: "Let's start SESSION 1"

**What we'll build in Session 1**:
- Project directory structure
- Basic Flask server
- Configuration system
- First checkpoint: server running at http://localhost:5000/api/health

**Time estimate**: 30-45 minutes

**You'll need**:
- Python 3.7+ installed
- Text editor (VS Code, Sublime, or any editor)
- Terminal/command line access

**After Session 1**, you'll have a working foundation to build on!

---

## Plan Summary

This plan breaks down the project into **14 manageable sessions**, each with:
- Clear goals and tasks
- Testing checkpoints to verify progress
- Beginner-friendly explanations
- Specific files to create
- What you'll learn

**Core Features (Sessions 1-9)**: Basic display with weather, news, quotes, photos
**Enhanced Features (Sessions 10-11)**: Reddit & Google Photos integration
**Deployment (Sessions 12-14)**: Running on actual Raspberry Pi 2
**Future**: Voice assistant with LLM integration

Each session builds on the previous one, so you can stop/resume anytime and pick up where you left off.

---

## Requirements Summary

### Hardware Constraints
- **Device**: Raspberry Pi 2 (1GB RAM, quad-core ARM Cortex-A7 @ 900MHz)
- **Display**: 22" LG LCD monitor (~1920x1080)
- **Future**: Google Speaker integration for voice queries

### Features (MVP)
1. **Static Widgets** (always visible):
   - Current time & date
   - Weather (OpenWeatherMap API with user-provided coordinates)

2. **Rotating Content**:
   - News articles from RSS feeds, Reddit, Hacker News, Twitter
   - Photos from Google Photos
   - Inspirational quotes

3. **Future Features**:
   - Voice assistant (Google Speaker integration)
   - LLM-powered Q&A summaries
   - Display voice query responses on screen

### Technical Decisions

#### Architecture Choice: **Lightweight Python + Minimal Frontend**
Given Pi 2's resource constraints, we'll use:
- **Backend**: Flask (lighter than FastAPI, ~30-40MB memory)
- **Frontend**: Vanilla HTML/CSS/JS (no frameworks to minimize overhead)
- **Display**: Chromium in kiosk mode (~120-150MB with optimizations)
- **Data Caching**: SQLite for caching API responses
- **Background Tasks**: APScheduler for periodic data fetching

**Why this stack:**
- Flask + vanilla JS keeps memory under 200MB total
- SQLite prevents repeated API calls
- No heavy frameworks that would burden Pi 2
- Extensible for future voice assistant service

#### Future Voice Assistant Architecture
```
Google Speaker → Google Assistant API → Pi Flask Server
                                       ↓
                                   LLM API (OpenAI/Anthropic)
                                       ↓
                                   Format Response
                                       ↓
                                   Display on Screen
```

## Directory Structure

```
pi-disp/
├── backend/
│   ├── app.py                 # Flask application entry point
│   ├── config.py              # Configuration management
│   ├── data_fetchers/         # API integrations
│   │   ├── __init__.py
│   │   ├── weather.py         # OpenWeatherMap
│   │   ├── news.py            # RSS, Reddit, HN, Twitter
│   │   ├── photos.py          # Google Photos
│   │   ├── quotes.py          # Random quotes API
│   │   └── voice_assistant.py # Future: voice & LLM integration
│   ├── cache.py               # SQLite caching layer
│   ├── scheduler.py           # Background data refresh
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── index.html             # Main display page
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css      # Responsive layout
│   │   └── js/
│   │       ├── app.js         # Main frontend logic
│   │       └── rotator.js     # Content rotation logic
│   └── templates/             # Jinja2 templates if needed
├── config/
│   ├── config.yaml.example    # Example configuration
│   └── .env.example           # Environment variables template
├── scripts/
│   ├── setup.sh               # Initial Pi setup script
│   ├── install_service.sh     # Systemd service installer
│   └── start_kiosk.sh         # Launch Chromium in kiosk mode
├── systemd/
│   └── pi-display.service     # Systemd service file
├── data/
│   └── cache.db               # SQLite database (created at runtime)
├── README.md
└── .gitignore
```

## Multi-Session Development Plan

This project will be built incrementally across multiple sessions. Each session has clear goals, deliverables, and testing checkpoints.

---

### SESSION 1: Project Setup & Backend Foundation
**Goal**: Get the basic project structure, GitHub repo, and Flask server running

**Tasks**:
1. Create GitHub repository (public or private)
2. Clone repository locally
3. Create directory structure
4. Create `PLAN.md` - copy of this detailed plan
5. Set up `requirements.txt` with initial dependencies
6. Create `backend/config.py` - configuration loader
7. Create `backend/app.py` - minimal Flask server with test endpoint
8. Create `.gitignore` and basic `README.md`
9. Push initial commit to GitHub

**Deliverables**:
- GitHub repository created and initialized
- Detailed plan (PLAN.md) in repository
- Complete folder structure
- Flask server that runs and responds to `http://localhost:5000/api/health`
- Configuration file template
- All files committed and pushed to GitHub

**Testing Checkpoint**:
```bash
# Should work at end of session 1:
cd backend
pip install -r requirements.txt
python app.py
# Visit http://localhost:5000/api/health - should see {"status": "ok"}

# Verify GitHub
git remote -v  # Should show your GitHub repo
git log  # Should show initial commit
```

**Why This Session**: Foundation must be solid before adding features, and GitHub ensures we can track progress and collaborate

---

### SESSION 2: Weather Data Fetcher
**Goal**: Build first data fetcher and caching system

**Tasks**:
1. Create `backend/cache.py` - SQLite caching wrapper
2. Create `backend/data_fetchers/weather.py` - OpenWeatherMap integration
3. Add `/api/weather` endpoint to Flask app
4. Test with real API key

**Deliverables**:
- Working weather API that returns current weather
- Caching system that stores weather for 30 minutes
- Clear error messages if API key is missing/invalid

**Testing Checkpoint**:
```bash
# Add OpenWeatherMap API key to config
# Start Flask server
# Visit http://localhost:5000/api/weather
# Should see: {"temp": 72, "description": "Clear sky", ...}
# Second request should be served from cache (faster)
```

**What You'll Learn**:
- How API requests work
- How caching reduces API calls
- How to handle API errors gracefully

---

### SESSION 3: News Aggregation (RSS & Hacker News)
**Goal**: Add multiple news sources

**Tasks**:
1. Create `backend/data_fetchers/news.py`
2. Implement RSS feed parser (using `feedparser`)
3. Implement Hacker News API integration
4. Add `/api/news` endpoint that combines both sources
5. Cache news for 15 minutes

**Deliverables**:
- News endpoint returning array of articles
- Each article has: title, link, source, published_date
- Configurable RSS feed URLs in config.yaml

**Testing Checkpoint**:
```bash
# Visit http://localhost:5000/api/news
# Should see array: [
#   {title: "...", link: "...", source: "HackerNews", ...},
#   {title: "...", link: "...", source: "RSS: TechCrunch", ...}
# ]
```

**Why This Session**: Demonstrates aggregating multiple data sources

---

### SESSION 4: Quotes & Time Endpoints
**Goal**: Complete remaining backend data sources

**Tasks**:
1. Create `backend/data_fetchers/quotes.py`
2. Add `/api/quote` endpoint
3. Add `/api/time` endpoint (no external API needed)
4. Test all backend endpoints together

**Deliverables**:
- Quote endpoint with daily rotation
- Time endpoint with formatted date/time
- All 4 core endpoints working: weather, news, quote, time

**Testing Checkpoint**:
```bash
# All these should work:
curl http://localhost:5000/api/weather
curl http://localhost:5000/api/news
curl http://localhost:5000/api/quote
curl http://localhost:5000/api/time
```

**Milestone**: Backend MVP complete! ✅

---

### SESSION 5: Frontend - Basic HTML Layout
**Goal**: Create the display interface

**Tasks**:
1. Create `frontend/index.html` with grid layout
2. Create `frontend/static/css/style.css` with responsive design
3. Add header section (time/weather - always visible)
4. Add main content area (for rotating content)
5. Test layout on desktop browser

**Deliverables**:
- HTML page with proper grid layout
- CSS styling optimized for 1920x1080
- Static placeholder content to verify layout

**Testing Checkpoint**:
- Open `frontend/index.html` in browser
- Should see clean layout with header and content areas
- Resize window - layout should adapt

**What You'll Learn**:
- HTML structure basics
- CSS Grid layout
- Responsive design principles

---

### SESSION 6: Frontend - JavaScript API Integration
**Goal**: Connect frontend to backend

**Tasks**:
1. Create `frontend/static/js/app.js`
2. Fetch data from Flask API endpoints
3. Update DOM with real data
4. Add auto-refresh (time every minute, weather every 30 min)
5. Add error handling and loading states

**Deliverables**:
- Frontend displays live weather data
- Clock updates every minute
- Graceful error messages if backend is down

**Testing Checkpoint**:
```bash
# Start Flask backend in one terminal
python backend/app.py

# Open frontend/index.html in browser
# Should see real weather and updating clock
# Stop Flask server - should see error message on frontend
```

**What You'll Learn**:
- JavaScript fetch() API
- DOM manipulation
- Async/await patterns
- Error handling

---

### SESSION 7: Content Rotation System
**Goal**: Rotate between news, quotes, photos

**Tasks**:
1. Create `frontend/static/js/rotator.js`
2. Implement rotation logic (30-second intervals)
3. Add smooth CSS transitions
4. Cycle through: news articles → quote → (photos when ready)

**Deliverables**:
- Content automatically rotates every 30 seconds
- Smooth fade transitions between items
- User can see current rotation index

**Testing Checkpoint**:
- Open frontend with backend running
- Watch content rotate automatically
- Should cycle: news headline 1 → news 2 → news 3 → quote → repeat

**Milestone**: Frontend MVP complete! ✅

---

### SESSION 8: Background Scheduler
**Goal**: Auto-refresh data without frontend intervention

**Tasks**:
1. Create `backend/scheduler.py` using APScheduler
2. Schedule weather updates every 30 minutes
3. Schedule news updates every 15 minutes
4. Schedule quote updates daily
5. Integrate scheduler with Flask app

**Deliverables**:
- Backend automatically refreshes data in background
- Frontend always gets fresh data from cache
- Logs show when each refresh happens

**Testing Checkpoint**:
```bash
# Start Flask with scheduler
python backend/app.py
# Watch logs - should see "Refreshing weather..." every 30 min
# Frontend should never wait for API calls (served from cache)
```

**What You'll Learn**:
- Background task scheduling
- Asynchronous operations
- Logging best practices

---

### SESSION 9: Configuration & Setup Scripts
**Goal**: Make deployment easy

**Tasks**:
1. Create `config/config.yaml.example` with all settings
2. Create `scripts/setup.sh` for Pi setup
3. Create `scripts/start_kiosk.sh` for Chromium kiosk mode
4. Write comprehensive README with setup instructions

**Deliverables**:
- Example config file with comments
- One-command setup script
- Kiosk mode launcher
- Beginner-friendly README

**Testing Checkpoint**:
- Clone project to fresh directory
- Follow README instructions
- Should be able to set up without help

---

### SESSION 10: Reddit Integration
**Goal**: Add Reddit as news source

**Tasks**:
1. Install and configure PRAW library
2. Update `backend/data_fetchers/news.py` with Reddit support
3. Add Reddit credentials to config
4. Fetch top posts from configured subreddits

**Deliverables**:
- Reddit posts appear in news rotation
- Configurable subreddits in config.yaml
- Rate limiting to avoid API throttling

**Testing Checkpoint**:
```bash
# Add Reddit API credentials to config
# Restart backend
# Visit /api/news
# Should include Reddit posts alongside RSS/HN
```

---

### SESSION 11: Google Photos OAuth Setup
**Goal**: Display personal photos

**Tasks**:
1. Create Google Cloud project & enable Photos API
2. Implement OAuth flow in `backend/data_fetchers/photos.py`
3. Add `/api/photo` endpoint
4. Store and refresh OAuth tokens
5. Add photos to rotation cycle

**Deliverables**:
- One-time OAuth authentication flow
- Random photos from your Google Photos
- Token refresh logic (don't require re-auth)

**Testing Checkpoint**:
- Run OAuth flow (opens browser, grant permission)
- Visit /api/photo - should see your photo URL
- Restart server - should still work (token persisted)

**What You'll Learn**:
- OAuth 2.0 authentication
- Token management
- Google Cloud Console

---

### SESSION 12: Raspberry Pi Deployment
**Goal**: Get everything running on actual Pi 2

**Tasks**:
1. Transfer code to Raspberry Pi
2. Run setup scripts
3. Configure API keys for Pi
4. Test performance and optimize
5. Set up auto-start on boot

**Deliverables**:
- System running on Pi 2
- Auto-starts on power-on
- Displays on 22" monitor
- Chromium in kiosk mode

**Testing Checkpoint**:
- Reboot Pi - system should auto-start
- Monitor shows display without login
- Run `htop` - memory usage < 300MB

**Milestone**: Core system deployed on Pi! ✅

---

### SESSION 13: Memory & Performance Optimization
**Goal**: Ensure stable operation on Pi 2

**Tasks**:
1. Profile memory usage
2. Optimize Chromium flags for Pi 2
3. Reduce JavaScript memory footprint
4. Add monitoring/logging
5. Implement auto-restart on high memory

**Deliverables**:
- Memory usage under 300MB consistently
- CPU usage under 25% average
- System runs 24+ hours without issues

**Testing Checkpoint**:
- Let system run overnight
- Check logs next day - no crashes
- Monitor stays on, content keeps rotating

---

### SESSION 14: Systemd Service Setup
**Goal**: Production-ready deployment

**Tasks**:
1. Create `systemd/pi-display.service`
2. Configure auto-restart on failure
3. Set up logging to file
4. Add health check endpoint
5. Test service management commands

**Deliverables**:
- Systemd service installed
- Auto-restart on crash
- Logs saved to `/var/log/pi-display/`
- Can control with `systemctl`

**Testing Checkpoint**:
```bash
sudo systemctl status pi-display  # Should show "active (running)"
sudo systemctl restart pi-display # Should restart cleanly
# Kill Flask process - should auto-restart
```

**Milestone**: Production-ready system! ✅

---

### FUTURE SESSIONS: Voice Assistant Integration
**Goal**: Add Google Speaker + LLM Q&A

**High-Level Plan** (detailed planning when ready):
1. Google Assistant SDK integration
2. Wake word detection
3. Speech-to-text processing
4. LLM API integration (OpenAI/Anthropic/other)
5. Response formatting for display
6. Voice query UI overlay
7. Audio feedback
8. Query history and caching

**Prerequisites**:
- Core system stable and running well
- Decision made on LLM provider
- Google Speaker hardware connected

**Note**: This is Phase 3, tackled after main system is solid

---

## Session Progress Tracking

**How to use this plan across sessions**:
1. At start of each session, say "Let's work on SESSION X"
2. Complete all tasks in that session
3. Run the testing checkpoint before moving on
4. If checkpoint fails, debug before proceeding
5. Mark session complete in your notes

**Current Session**: Not started (begin with SESSION 1)

**Completed Sessions**: None yet

---

## Quick Reference: Session Dependencies

```
SESSION 1 (Foundation)
    ↓
SESSION 2 (Weather + Caching) ← Must work before continuing
    ↓
SESSION 3 (News RSS/HN)
    ↓
SESSION 4 (Quotes + Time)  ← Backend MVP checkpoint
    ↓
SESSION 5 (Frontend HTML)
    ↓
SESSION 6 (Frontend JS)
    ↓
SESSION 7 (Rotation)  ← Frontend MVP checkpoint
    ↓
SESSION 8 (Scheduler)
    ↓
SESSION 9 (Config/Scripts)
    ↓
SESSION 10 (Reddit) ← Can be done anytime after Session 3
    ↓
SESSION 11 (Google Photos) ← Independent, can be done anytime
    ↓
SESSION 12 (Pi Deployment) ← Requires Sessions 1-9 complete
    ↓
SESSION 13 (Optimization) ← Do on actual Pi
    ↓
SESSION 14 (Systemd) ← Production ready!
```

---

## Returning After a Break?

If you're returning to this project after days/weeks:

1. **Check what's working**:
   ```bash
   # Start backend
   cd backend && python app.py

   # Test all endpoints
   curl http://localhost:5000/api/health
   curl http://localhost:5000/api/weather
   curl http://localhost:5000/api/news
   curl http://localhost:5000/api/quote
   curl http://localhost:5000/api/time
   ```

2. **Open frontend**: Check if frontend displays correctly

3. **Review last session**: Look at last completed session in this plan

4. **Continue from**: Next session in sequence

5. **Ask**: "Where did we leave off?" - I'll help you resume!

---

## Code Quality Guidelines (for Beginner-Friendly Development)

Since this is for a beginner:
- **Extensive comments**: Every function will have docstrings explaining what it does
- **Step-by-step explanations**: Comments explaining why we're doing things
- **Simple patterns**: Avoid overly clever code, prefer readable over concise
- **Error messages**: Clear, helpful error messages that explain what went wrong
- **README sections**: Each major component gets explanation in README
- **Setup scripts**: Automated setup to minimize manual configuration
- **Troubleshooting guide**: Common issues and solutions documented

**Code Comment Example**:
```python
def fetch_weather(lat, lon):
    """
    Fetch current weather from OpenWeatherMap API.

    Why we cache: API allows 1000 calls/day. With weather updating
    every 30 min, that's 48 calls/day - well within limits.

    Args:
        lat (float): Latitude coordinate
        lon (float): Longitude coordinate

    Returns:
        dict: Weather data with temp, description, humidity, etc.

    Raises:
        APIError: If OpenWeatherMap returns error
        ConfigError: If API key is missing
    """
    # Check if we have valid API key
    if not config.get('weather.api_key'):
        raise ConfigError("OpenWeatherMap API key not found in config")

    # Rest of function...
```

---

## Detailed Implementation Steps (For Reference)

### Phase 1: Backend Foundation
**Files to create:**
- `backend/app.py` - Flask server with API endpoints
- `backend/config.py` - Load from YAML/env vars
- `backend/cache.py` - SQLite caching wrapper
- `backend/requirements.txt` - Dependencies

**API Endpoints:**
- `GET /api/time` - Current time/date
- `GET /api/weather` - Weather data
- `GET /api/news` - Aggregated news from all sources
- `GET /api/photo` - Random photo from Google Photos
- `GET /api/quote` - Random quote
- `GET /api/voice` (future) - Voice query response

### Phase 2: Data Fetchers
**Files to create:**
- `backend/data_fetchers/weather.py`
  - OpenWeatherMap API integration
  - Cache for 30 minutes

- `backend/data_fetchers/news.py`
  - RSS feed parser (feedparser library)
  - Reddit API (PRAW library)
  - Hacker News API (requests)
  - Twitter (tweepy or nitter scraping)
  - Cache for 15 minutes

- `backend/data_fetchers/photos.py`
  - Google Photos API with OAuth2
  - Token storage and refresh
  - Cache photo URLs for 1 hour

- `backend/data_fetchers/quotes.py`
  - Random quote API (zenquotes or quotable)
  - Cache daily

### Phase 3: Background Scheduler
**File to create:**
- `backend/scheduler.py`
  - APScheduler to refresh data periodically
  - Weather: every 30 min
  - News: every 15 min
  - Photos: every hour
  - Quotes: daily

### Phase 4: Frontend Display
**Files to create:**
- `frontend/index.html`
  - Grid layout: fixed header with time/weather
  - Main content area for rotating items
  - Responsive design for 1920x1080

- `frontend/static/css/style.css`
  - Clean, readable fonts (optimized for distance viewing)
  - Grid layout with flexbox
  - Smooth transitions

- `frontend/static/js/app.js`
  - Fetch data from backend API
  - Update DOM every minute (time)
  - Update weather every 30 min

- `frontend/static/js/rotator.js`
  - Rotate between news, photos, quotes
  - Configurable rotation interval (e.g., 30 seconds)
  - Smooth fade transitions

### Phase 5: Configuration & Setup
**Files to create:**
- `config/config.yaml.example`
  ```yaml
  weather:
    api_key: "YOUR_OPENWEATHERMAP_KEY"
    latitude: 0.0
    longitude: 0.0

  news:
    rss_feeds:
      - "https://example.com/feed"
    reddit_subreddits:
      - "worldnews"
    twitter_enabled: false

  photos:
    google_credentials_file: "path/to/credentials.json"

  display:
    rotation_interval: 30  # seconds
  ```

- `.env.example`
  - API keys and secrets

- `scripts/setup.sh`
  - Install system dependencies (Chromium, Python 3)
  - Install Python packages
  - Configure autostart

- `scripts/start_kiosk.sh`
  - Launch Chromium in kiosk mode
  - Disable screen blanking
  - Auto-reload on crash

- `systemd/pi-display.service`
  - Systemd service for Flask backend
  - Auto-restart on failure
  - Start on boot

### Phase 6: Google Photos OAuth Setup
**Implementation:**
1. Create Google Cloud project
2. Enable Photos Library API
3. Create OAuth2 credentials (Desktop app)
4. Download credentials.json
5. First-time auth flow (run on Pi, opens browser)
6. Store refresh token in config
7. Auto-refresh access token in code

### Phase 7: Future Voice Assistant Extension
**Files to add later:**
- `backend/data_fetchers/voice_assistant.py`
  - Google Assistant SDK integration
  - LLM API client (OpenAI/Anthropic)
  - Response formatting

- Frontend updates:
  - Voice query display overlay
  - Audio visualizer while listening
  - Formatted LLM response display

**Architecture considerations:**
- Voice query → trigger Flask endpoint
- Call LLM API with query context
- Stream/display response on screen
- Cache recent queries
- Consider rate limiting on Pi 2

## Technology Stack

### Python Dependencies
```
Flask==3.0.0
requests==2.31.0
feedparser==6.0.11
praw==7.7.1            # Reddit
tweepy==4.14.0         # Twitter (if API available)
google-auth==2.25.0
google-auth-oauthlib==1.2.0
google-api-python-client==2.110.0
APScheduler==3.10.4
PyYAML==6.0.1
python-dotenv==1.0.0
```

### System Dependencies (Pi 2)
```
sudo apt-get install chromium-browser unclutter python3-pip sqlite3
```

### Memory Optimization for Pi 2
- Limit Chromium flags: `--disable-gpu --disable-software-rasterizer --disable-dev-shm-usage`
- Flask: Use production WSGI server (gunicorn with 1-2 workers)
- Cache aggressively to minimize API calls
- Lazy load images
- Limit concurrent API requests

## API Key Requirements

1. **OpenWeatherMap** - https://openweathermap.org/api
   - Free tier: 1,000 calls/day
   - Get API key from account dashboard

2. **Google Photos** - https://console.cloud.google.com
   - Create project
   - Enable Photos Library API
   - OAuth 2.0 credentials

3. **Reddit** - https://www.reddit.com/prefs/apps
   - Create app for PRAW
   - Get client_id and client_secret

4. **Twitter** - https://developer.twitter.com
   - Note: API access currently restricted/paid
   - Alternative: Nitter scraping or skip

5. **Quotes** - No key needed for most free APIs

6. **Future LLM** - OpenAI or Anthropic API key (configurable, to be decided later)

## Deployment Steps

1. **Prepare Pi:**
   ```bash
   sudo apt-get update && sudo apt-get upgrade
   ./scripts/setup.sh
   ```

2. **Configure:**
   - Copy `config.yaml.example` to `config/config.yaml`
   - Add API keys and coordinates
   - Run Google Photos OAuth flow

3. **Install service:**
   ```bash
   ./scripts/install_service.sh
   sudo systemctl enable pi-display
   sudo systemctl start pi-display
   ```

4. **Launch display:**
   - Add to `~/.config/lxsession/LXDE-pi/autostart`:
     ```
     @/path/to/scripts/start_kiosk.sh
     ```

5. **Verify:**
   - Check Flask is running: `http://localhost:5000`
   - Display should auto-load in Chromium

## Performance Considerations for Pi 2

- **Memory Budget**:
  - Flask + workers: ~60MB
  - Chromium kiosk: ~120MB
  - Total: ~180MB (leaves ~800MB for OS)

- **CPU Optimization**:
  - Offload image resizing to backend
  - Minimize JavaScript animations
  - Use CSS transitions over JS

- **Network**:
  - Batch API calls when possible
  - Cache everything
  - Background refresh (don't block UI)

## Testing Plan

1. **Backend**: Test each data fetcher independently
2. **Caching**: Verify cache hits/misses
3. **Frontend**: Test on desktop browser first
4. **Integration**: Test on Pi 2 with full load
5. **Long-running**: 24-hour stability test

## Future Enhancements

1. **Voice Assistant** (priority):
   - Google Speaker integration
   - LLM summarization
   - Display on screen

2. **Additional features**:
   - Calendar/reminders integration
   - Stock/crypto tickers
   - Spotify now playing
   - Smart home status

3. **Personalization**:
   - Multiple screens/profiles
   - Schedule-based content (work hours vs evening)
   - Manual content refresh buttons

## Risk Mitigation

- **API Failures**: Graceful fallbacks, show cached data
- **OAuth Expiry**: Auto-refresh tokens, notify on failure
- **Memory Issues**: Monitor and auto-restart if > 90% usage
- **Network Loss**: Show "offline" indicator, retry logic

## Success Criteria

- [ ] Display boots automatically on Pi power-on
- [ ] All widgets update reliably
- [ ] System runs stable for 7+ days
- [ ] Memory usage < 300MB
- [ ] CPU usage < 25% average
- [ ] Graceful handling of API failures
- [ ] Easy to add new data sources

---

## Key Concepts Explained (for Beginners)

### What is an API?
**API (Application Programming Interface)** is a way for programs to talk to each other. When we want weather data, we send a request to OpenWeatherMap's API, and they send back the data.

**Example**: Like ordering food at a restaurant - you (the app) ask the waiter (API) for food, and the kitchen (server) makes it and sends it back.

### What is Caching?
**Caching** means storing data temporarily so you don't have to fetch it again immediately.

**Why we cache**:
- APIs have limits (e.g., OpenWeatherMap: 1000 calls/day)
- Fetching data takes time and internet bandwidth
- Weather doesn't change every second

**Example**: If you check weather at 2:00 PM, we save that data. If you check again at 2:05 PM, we show the saved data instead of asking the API again.

### What is Flask?
**Flask** is a Python library that makes it easy to build web servers.

**Our use**: Flask provides the backend API that the frontend calls. When frontend wants weather, it asks Flask, and Flask either gets it from cache or fetches from OpenWeatherMap.

### What is the Frontend vs Backend?
**Frontend** = What you see (HTML, CSS, JavaScript in the browser)
**Backend** = The server that provides data (Python Flask)

**Our architecture**:
```
Browser (Frontend)  ←→  Flask (Backend)  ←→  External APIs
   [HTML/CSS/JS]        [Python Server]       [Weather, News, etc.]
```

### What is OAuth?
**OAuth** is a secure way to let one app access your data from another app without sharing your password.

**Our use**: Google Photos OAuth lets our Pi access your photos without storing your Google password. You authorize once, and we get a "token" that lets us access photos.

### What is a Systemd Service?
**Systemd** is Linux's system manager. A "service" is a program that runs in the background.

**Our use**: We create a service so Flask starts automatically when Pi boots, and restarts if it crashes.

### What is Kiosk Mode?
**Kiosk mode** is when a browser runs fullscreen without toolbars, address bars, or any browser UI.

**Our use**: Chromium runs in kiosk mode on the Pi so the display looks like a dedicated device, not a web browser.

---

## Common Issues & Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'flask'"
**Cause**: Python package not installed
**Fix**:
```bash
pip install -r requirements.txt
```

### Issue: "Connection refused" when accessing http://localhost:5000
**Cause**: Flask server not running
**Fix**:
```bash
cd backend
python app.py
# Should see: "Running on http://127.0.0.1:5000"
```

### Issue: API returns 401 Unauthorized
**Cause**: Invalid or missing API key
**Fix**:
1. Check `config/config.yaml` has correct API key
2. Verify key is valid on the API provider's website
3. Check for extra spaces or quotes in config

### Issue: Weather shows old data
**Cause**: Cache not expiring properly
**Fix**:
```bash
# Delete cache database
rm data/cache.db
# Restart Flask - will create fresh cache
```

### Issue: "CORS error" in browser console
**Cause**: Frontend trying to access Flask from different origin
**Fix**: We'll add Flask-CORS in Session 6 to handle this

### Issue: Pi display shows black screen after boot
**Cause**: Chromium kiosk script not running
**Fix**:
1. Check `~/.config/lxsession/LXDE-pi/autostart` has correct path
2. Test script manually: `./scripts/start_kiosk.sh`
3. Check script has execute permissions: `chmod +x scripts/start_kiosk.sh`

### Issue: High memory usage on Pi 2
**Cause**: Too many Chromium processes or memory leaks
**Fix**: Session 13 covers optimization, including:
- Chromium flags to reduce memory
- Limiting workers
- Auto-restart on high memory

### Issue: Google Photos OAuth error "Redirect URI mismatch"
**Cause**: OAuth redirect URL doesn't match Google Cloud Console settings
**Fix**: Make sure redirect URI in Google Console matches exactly what's in code (usually `http://localhost:5000/oauth/callback`)

---

## GitHub Repository Setup

### Creating the Repository

**Step 1: Create on GitHub.com**
1. Go to https://github.com/new
2. Repository name: `pi-display` (or your preferred name)
3. Description: "Raspberry Pi information display with weather, news, photos, and quotes"
4. Choose Public or Private
5. **DO NOT** initialize with README, .gitignore, or license (we'll create these)
6. Click "Create repository"

**Step 2: Initialize Locally**
```bash
# In your pi-disp directory
cd /Users/in22904092/Documents/CodeBase/misc/pi-disp

# Initialize git
git init

# Create .gitignore first (see below)
# Create initial files
# Add this plan as PLAN.md

# Stage all files
git add .

# First commit
git commit -m "Initial commit - project structure and detailed plan"

# Add GitHub as remote (replace YOUR_USERNAME and YOUR_REPO)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Step 3: Verify**
```bash
# Check remote
git remote -v

# View commit history
git log

# Visit your GitHub repo in browser
# Should see all files including PLAN.md
```

### Git Best Practices for This Project

**After Each Session**:
```bash
# Add files from session
git add .

# Commit with session number
git commit -m "SESSION X: [description]"

# Push to GitHub
git push

# Examples:
# "SESSION 1: Project foundation and Flask setup"
# "SESSION 2: Weather fetcher and caching system"
# "SESSION 3: News aggregation (RSS + Hacker News)"
```

**Why this helps**:
- Remote backup of all your work
- Can access from anywhere (laptop, Pi, etc.)
- Can revert if something breaks
- Clear history of what was added when
- Easy to see what changed between sessions
- Can share progress or get help

**Files to NEVER commit** (add to `.gitignore`):
```gitignore
# API keys and secrets - NEVER commit these!
config/config.yaml
.env
credentials.json
token.json

# Cache and data
data/cache.db
data/*.db
*.db

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.venv/
venv/
env/
ENV/

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
*.log
logs/
```

### Repository Structure on GitHub

Your repository will look like this:

```
pi-display/  (GitHub repo)
├── PLAN.md                    # This detailed plan
├── README.md                  # User-facing documentation
├── .gitignore                 # Files to exclude from git
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── cache.py
│   ├── scheduler.py
│   ├── requirements.txt
│   └── data_fetchers/
│       ├── __init__.py
│       ├── weather.py
│       ├── news.py
│       ├── photos.py
│       ├── quotes.py
│       └── voice_assistant.py (future)
├── frontend/
│   ├── index.html
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           ├── app.js
│           └── rotator.js
├── config/
│   ├── config.yaml.example    # Template (safe to commit)
│   └── .env.example           # Template (safe to commit)
├── scripts/
│   ├── setup.sh
│   ├── install_service.sh
│   └── start_kiosk.sh
├── systemd/
│   └── pi-display.service
└── data/                      # Created at runtime, not in git
    └── cache.db
```

### Cloning on Raspberry Pi

When ready to deploy to Pi (Session 12):
```bash
# SSH into your Pi
ssh pi@raspberrypi.local

# Clone your repo
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

# Copy and configure settings
cp config/config.yaml.example config/config.yaml
# Edit config.yaml with your API keys

# Run setup script
./scripts/setup.sh
```

---

## Resources & Documentation

### Python & Flask
- **Flask Documentation**: https://flask.palletsprojects.com/
- **Python Tutorial**: https://docs.python.org/3/tutorial/
- **Flask Mega-Tutorial**: https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world

### Frontend
- **HTML/CSS Basics**: https://developer.mozilla.org/en-US/docs/Learn
- **JavaScript Fetch API**: https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API
- **CSS Grid Guide**: https://css-tricks.com/snippets/css/complete-guide-grid/

### APIs We're Using
- **OpenWeatherMap**: https://openweathermap.org/api
- **Hacker News API**: https://github.com/HackerNews/API
- **Reddit API (PRAW)**: https://praw.readthedocs.io/
- **Google Photos API**: https://developers.google.com/photos

### Raspberry Pi
- **Pi Setup Guide**: https://www.raspberrypi.com/documentation/
- **Chromium Kiosk Mode**: https://pimylifeup.com/raspberry-pi-kiosk/
- **Systemd Services**: https://www.raspberrypi.com/documentation/computers/using_linux.html#the-systemd-daemon

### Troubleshooting
- **Flask Debug Mode**: Add `debug=True` to `app.run()` for detailed errors
- **Browser DevTools**: Press F12 to see JavaScript errors and network requests
- **Pi Logs**: Use `journalctl -u pi-display -f` to see service logs

---

## Notes for Each Session

### Pre-Session Checklist
- [ ] Read session goals and tasks
- [ ] Understand what we're building
- [ ] Have any needed API keys ready
- [ ] Previous session's checkpoint passed

### During Session
- Ask questions if anything is unclear
- Test code as we write it
- Don't skip the "What You'll Learn" sections
- Read code comments carefully

### Post-Session Checklist
- [ ] All files created
- [ ] Testing checkpoint passed
- [ ] Code committed to git
- [ ] Understand what was built
- [ ] Ready for next session

---

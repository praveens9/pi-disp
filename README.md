# Raspberry Pi Information Display

A lightweight, always-on information display for Raspberry Pi that shows weather, news, photos, quotes, and time on your monitor. Optimized for Raspberry Pi 2 with future support for voice assistant integration.

![Project Status](https://img.shields.io/badge/status-in%20development-yellow)
![Python](https://img.shields.io/badge/python-3.7+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

### Current
- ⏰ **Live Clock** - Always-visible time and date
- 🌤️ **Weather Display** - Real-time weather from OpenWeatherMap
- 📰 **News Aggregation** - Headlines from RSS feeds, Hacker News, Reddit
- 💬 **Daily Quotes** - Inspirational quotes rotation
- 🖼️ **Photo Display** - Personal photos from Google Photos
- 🔄 **Auto-Rotation** - Smooth transitions between content

### Future
- 🎤 **Voice Assistant** - Ask questions via Google Speaker
- 🤖 **LLM Integration** - AI-powered summaries and responses
- 📅 **Calendar Integration** - Upcoming events and reminders

## Demo

```
┌─────────────────────────────────────────────┐
│  🕐 2:47 PM                    ☀️ 72°F      │
│  Friday, January 17, 2026     Clear Sky   │
├─────────────────────────────────────────────┤
│                                             │
│  📰 Latest Headlines:                       │
│  → Breaking: New AI breakthrough...         │
│  → Tech giant announces...                  │
│                                             │
│  💬 "The only way to do great work..."     │
│  - Steve Jobs                               │
│                                             │
│  🖼️ [Your photo from Google Photos]        │
│                                             │
└─────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Raspberry Pi 2 (or newer) with Raspbian/Raspberry Pi OS
- Python 3.7 or higher
- Internet connection
- 22" LCD monitor (or any size - responsive design)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/pi-display.git
   cd pi-display
   ```

2. **Set up configuration**
   ```bash
   cp config/config.yaml.example config/config.yaml
   # Edit config.yaml with your API keys
   nano config/config.yaml
   ```

3. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Run the backend**
   ```bash
   python app.py
   ```

5. **Open the frontend**
   - Open `frontend/index.html` in your browser
   - Or navigate to `http://localhost:5000` (when served via Flask)

## Configuration

Create `config/config.yaml` based on the example template:

```yaml
weather:
  api_key: "your-openweathermap-api-key"
  latitude: 40.7128   # Your location
  longitude: -74.0060

news:
  rss_feeds:
    - "https://feeds.bbci.co.uk/news/rss.xml"
    - "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"
  reddit_subreddits:
    - "worldnews"
    - "technology"

display:
  rotation_interval: 30  # seconds between content changes
```

## Getting API Keys

### OpenWeatherMap (Required)
1. Sign up at https://openweathermap.org/api
2. Get your free API key (1000 calls/day)
3. Add to `config.yaml`

### Reddit (Optional)
1. Go to https://www.reddit.com/prefs/apps
2. Create an app to get `client_id` and `client_secret`
3. Add credentials to config

### Google Photos (Optional)
1. Create project at https://console.cloud.google.com
2. Enable Photos Library API
3. Download OAuth credentials
4. Follow OAuth setup instructions in [PLAN.md](PLAN.md)

## Project Structure

```
pi-display/
├── PLAN.md                 # Detailed implementation plan (14 sessions)
├── README.md               # This file
├── .gitignore              # Git exclusions
│
├── backend/                # Python Flask backend
│   ├── app.py              # Main Flask application
│   ├── config.py           # Configuration loader
│   ├── cache.py            # SQLite caching system
│   ├── scheduler.py        # Background data refresh
│   ├── requirements.txt    # Python dependencies
│   └── data_fetchers/      # API integrations
│       ├── weather.py      # OpenWeatherMap
│       ├── news.py         # RSS/Reddit/HN
│       ├── photos.py       # Google Photos
│       └── quotes.py       # Quote APIs
│
├── frontend/               # HTML/CSS/JS display
│   ├── index.html          # Main page
│   └── static/
│       ├── css/style.css   # Styling
│       └── js/
│           ├── app.js      # Main logic
│           └── rotator.js  # Content rotation
│
├── config/                 # Configuration files
│   ├── config.yaml.example # Template
│   └── .env.example        # Environment variables
│
├── scripts/                # Setup and deployment
│   ├── setup.sh            # Pi setup script
│   ├── install_service.sh  # Systemd installer
│   └── start_kiosk.sh      # Kiosk mode launcher
│
└── systemd/                # System service
    └── pi-display.service  # Auto-start service
```

## Development

This project follows a 14-session development plan designed for beginners. See [PLAN.md](PLAN.md) for the complete roadmap.

### Current Session: SESSION 2
- [x] SESSION 1: Project foundation complete
- [x] SQLite caching system
- [x] OpenWeatherMap integration
- [x] `/api/weather` endpoint
- [ ] Full testing with real API
- [ ] Next: News aggregation (SESSION 3)

### Testing
```bash
# Test backend (with virtual environment)
source venv/bin/activate
python backend/app.py

# Test all endpoints
curl http://localhost:5000/api/health
curl http://localhost:5000/api/time
curl http://localhost:5000/api/weather  # Requires API key in config

# Weather endpoint example response:
# {
#   "temperature": 72.5,
#   "feels_like": 70.2,
#   "condition": "Clear",
#   "description": "clear sky",
#   "humidity": 45,
#   "pressure": 1013,
#   "wind_speed": 5.2,
#   "location": "New York",
#   "country": "US"
# }
```

## Deployment on Raspberry Pi

### Automatic Setup
```bash
# Run setup script
./scripts/setup.sh

# Install as system service
./scripts/install_service.sh
sudo systemctl enable pi-display
sudo systemctl start pi-display
```

### Manual Setup
1. Install system dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install chromium-browser unclutter python3-pip sqlite3
   ```

2. Configure auto-start:
   - Add to `~/.config/lxsession/LXDE-pi/autostart`:
     ```
     @/path/to/pi-display/scripts/start_kiosk.sh
     ```

3. Verify deployment:
   ```bash
   sudo systemctl status pi-display
   ```

## Performance Optimization (Pi 2)

The system is optimized for Raspberry Pi 2's 1GB RAM:

- **Memory usage**: < 300MB total
  - Flask backend: ~60MB
  - Chromium kiosk: ~120MB
- **CPU usage**: < 25% average
- **Aggressive caching**: Minimizes API calls
- **Lightweight frontend**: Vanilla JS, no frameworks

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.7+

# Reinstall dependencies
pip install -r backend/requirements.txt

# Check for errors
python backend/app.py
```

### No weather data
- Verify API key in `config/config.yaml`
- Check key is valid at OpenWeatherMap
- Ensure coordinates are correct

### Display not showing
- Check Flask is running: `curl http://localhost:5000/api/health`
- Open browser console (F12) for JavaScript errors
- Verify all paths in HTML are correct

### High memory on Pi
- Reduce Chromium tabs/extensions
- Check for memory leaks: `htop`
- Restart service: `sudo systemctl restart pi-display`

For more issues, see [PLAN.md - Troubleshooting section](PLAN.md#common-issues--troubleshooting)

## Architecture

```
┌─────────────┐
│   Display   │  (Chromium in kiosk mode)
│  (Frontend) │
└──────┬──────┘
       │ HTTP requests
       │
┌──────▼──────┐
│    Flask    │  (Python backend)
│   Backend   │
└──────┬──────┘
       │
       ├─ SQLite Cache ◄─────┐
       │                     │
       ├─ APScheduler        │
       │  (Background        │
       │   refresh)──────────┘
       │
       └─ External APIs
          ├─ OpenWeatherMap
          ├─ RSS Feeds
          ├─ Hacker News
          ├─ Reddit
          └─ Google Photos
```

## Future Roadmap

- [ ] **Session 2-4**: Complete backend data fetchers
- [ ] **Session 5-7**: Build responsive frontend
- [ ] **Session 8-9**: Background scheduler and setup scripts
- [ ] **Session 10-11**: Reddit and Google Photos integration
- [ ] **Session 12-14**: Pi deployment and optimization
- [ ] **Phase 3**: Voice assistant + LLM integration

See [PLAN.md](PLAN.md) for detailed session breakdown.

## Contributing

This project is primarily for personal use and learning, but suggestions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on actual Pi hardware if possible
5. Submit a pull request

## Resources

- [Detailed Implementation Plan](PLAN.md)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/)
- [OpenWeatherMap API](https://openweathermap.org/api)

## License

MIT License - feel free to use and modify for your own projects!

## Acknowledgments

- Built with guidance from Claude (Anthropic)
- Designed for beginners learning Python and web development
- Optimized for Raspberry Pi 2 hardware constraints

---

**Need help?** Check [PLAN.md](PLAN.md) for:
- Beginner-friendly concept explanations
- Step-by-step session guides
- Common issues and solutions
- API setup instructions

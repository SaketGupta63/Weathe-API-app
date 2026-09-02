# 🌤️ Weather App

A simple desktop weather lookup application built with **Python** and **PyQt5**, using the [OpenWeatherMap API](https://openweathermap.org/api) to fetch real-time weather data for any city.

![Python](https://img.shields.io/badge/Python-3.x-blue)
![PyQt5](https://img.shields.io/badge/GUI-PyQt5-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## Features

- 🔍 Search current weather by city name
- 🌡️ Displays temperature in Celsius
- ☁️ Weather condition emoji based on OpenWeatherMap condition codes
- ⚠️ Graceful error handling for invalid cities and network failures
- 🎨 Custom UI styling via Qt Style Sheets (QSS)

## Tech Stack

- **Python 3**
- **PyQt5** — GUI framework
- **Requests** — HTTP client for API calls
- **OpenWeatherMap API** — weather data source

## Preview
![](https://i.ibb.co/fzxNzs2P/Screenshot-2026-09-01-121512.png)
![](https://i.ibb.co/4RKB4hB8/Screenshot-2026-09-01-121524.png)

## How It Works

1. User enters a city name and clicks **Get Weather**.
2. The app sends a `GET` request to OpenWeatherMap's `/weather` endpoint with the city name, API key, and metric units.
3. The JSON response is parsed:
   - On success, temperature, description, and a matching emoji are displayed.
   - On failure (invalid city, network error), an error message is shown instead.

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/weather-app.git
cd weather-app

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install PyQt5 requests
```

## Usage

1. Get a free API key from [OpenWeatherMap](https://openweathermap.org/api).
2. Set it as an environment variable (recommended) instead of hardcoding it:
   ```bash
   export OWM_API_KEY="your_api_key_here"   # macOS/Linux
   setx OWM_API_KEY "your_api_key_here"      # Windows
   ```
3. Run the app:
   ```bash
   python weather_app.py
   ```

## Project Structure

```
weather-app/
├── weather_app.py     # Main application file
├── README.md
└── requirements.txt
```

## Lessons Learned

This project was a hands-on exercise in:
- Event-driven GUI programming (Qt's signal/slot mechanism)
- REST API integration and JSON parsing
- Defensive error handling for network requests
- Separating concerns between data fetching, business logic, and UI rendering

## Future Improvements

- [ ] Move API calls off the main thread to keep the UI responsive
- [ ] Add 5-day forecast view
- [ ] Support for Fahrenheit/Celsius toggle
- [ ] Remember last searched city
- [ ] Package as a standalone executable

## License

This project is licensed under the MIT License.

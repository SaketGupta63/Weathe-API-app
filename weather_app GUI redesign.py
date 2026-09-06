import sys
import requests
from datetime import datetime
from collections import defaultdict

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFrame
)
from PyQt5.QtGui import QPixmap, QPalette, QLinearGradient, QColor, QGradient
from PyQt5.QtCore import Qt


class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()
        self.api_key = "adf13248bd2af81b250ebc793c9458ff"
        self.units = "metric"        # "metric" -> Celsius, "imperial" -> Fahrenheit
        self.last_city = ""          # remembered so the unit toggle can re-fetch

        # --- current weather widgets ---
        self.city_label = QLabel("Enter City:", self)
        self.city_input = QLineEdit(self)
        self.get_weather_button = QPushButton("Get Weather", self)
        self.unit_toggle_button = QPushButton("°C", self)
        self.temperature_label = QLabel(self)
        self.icon_label = QLabel(self)
        self.description_label = QLabel(self)

        # --- forecast widgets: 5 day "cards" ---
        self.forecast_cards = []  # list of dicts: {frame, day, icon, temp}
        for _ in range(5):
            frame = QFrame(self)
            frame.setObjectName("forecast_card")
            self.forecast_cards.append({
                "frame": frame,
                "day": QLabel(frame),
                "icon": QLabel(frame),
                "temp": QLabel(frame),
            })

        self.init_ui()
        self.apply_theme(800)  # neutral "clear sky" theme as the default look

    def init_ui(self):
        self.setWindowTitle("Weather App")
        self.setMinimumSize(520, 480)
        self.resize(650, 560)

        vbox = QVBoxLayout()
        vbox.setContentsMargins(30, 30, 30, 30)
        vbox.setSpacing(14)

        vbox.addWidget(self.city_label)
        vbox.addWidget(self.city_input)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        button_row.addWidget(self.get_weather_button, 3)
        button_row.addWidget(self.unit_toggle_button, 1)
        vbox.addLayout(button_row)

        vbox.addWidget(self.temperature_label)
        vbox.addWidget(self.icon_label)
        vbox.addWidget(self.description_label)

        # forecast cards in a grid (row 0 today; leaves room to add a second
        # row of details like humidity/wind later without restructuring)
        forecast_grid = QGridLayout()
        forecast_grid.setHorizontalSpacing(12)
        for col, card in enumerate(self.forecast_cards):
            card_layout = QVBoxLayout(card["frame"])
            card_layout.setContentsMargins(8, 12, 8, 12)
            card_layout.setSpacing(4)
            card_layout.addWidget(card["day"])
            card_layout.addWidget(card["icon"])
            card_layout.addWidget(card["temp"])
            forecast_grid.addWidget(card["frame"], 0, col)
        vbox.addLayout(forecast_grid)

        self.setLayout(vbox)

        # --- alignment ---
        self.city_label.setAlignment(Qt.AlignCenter)
        self.city_input.setAlignment(Qt.AlignCenter)
        self.temperature_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.description_label.setAlignment(Qt.AlignCenter)
        for card in self.forecast_cards:
            card["day"].setAlignment(Qt.AlignCenter)
            card["icon"].setAlignment(Qt.AlignCenter)
            card["temp"].setAlignment(Qt.AlignCenter)

        # --- placeholder text + Enter-to-submit ---
        self.city_input.setPlaceholderText("e.g. London")
        self.city_input.returnPressed.connect(self.get_weather)

        # --- object names for styling ---
        self.city_label.setObjectName("city_label")
        self.city_input.setObjectName("city_input")
        self.get_weather_button.setObjectName("get_weather_button")
        self.unit_toggle_button.setObjectName("unit_toggle_button")
        self.temperature_label.setObjectName("temperature_label")
        self.icon_label.setObjectName("icon_label")
        self.description_label.setObjectName("description_label")
        for card in self.forecast_cards:
            card["day"].setObjectName("forecast_day_label")
            card["icon"].setObjectName("forecast_icon_label")
            card["temp"].setObjectName("forecast_temp_label")

        # NOTE: deliberately scoped to specific widget types (QLabel,
        # QPushButton, ...) rather than a blanket `QWidget { ... }` rule.
        # A `QWidget` selector would also match this top-level WeatherApp
        # widget and force Qt to paint its background via the stylesheet,
        # which would silently cover up the QPalette gradient set in
        # apply_theme(). Keeping the top-level widget outside the
        # stylesheet's reach is what lets the two systems (stylesheet for
        # child widgets, palette for the window background) coexist.
        self.setStyleSheet("""
            QLabel, QPushButton, QLineEdit, QFrame {
                font-family: Arial, sans-serif;
            }
            QLabel {
                color: white;
            }
            QLabel#city_label {
                font-size: 32px;
                font-style: italic;
            }
            QLineEdit#city_input {
                font-size: 28px;
                padding: 6px;
                border-radius: 8px;
                background-color: rgba(255, 255, 255, 0.85);
                color: #222;
            }
            QPushButton {
                font-size: 20px;
                font-weight: bold;
                padding: 10px;
                border-radius: 8px;
                color: white;
                background-color: rgba(255, 255, 255, 0.20);
                border: 1px solid rgba(255, 255, 255, 0.4);
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.35);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.10);
            }
            QLabel#temperature_label {
                font-size: 64px;
                font-weight: bold;
            }
            QLabel#icon_label {
                font-size: 64px;
                min-height: 90px;
            }
            QLabel#description_label {
                font-size: 26px;
                font-weight: bold;
            }
            QFrame#forecast_card {
                background-color: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 10px;
            }
            QLabel#forecast_day_label {
                font-size: 15px;
                font-weight: bold;
            }
            QLabel#forecast_icon_label {
                font-size: 28px;
            }
            QLabel#forecast_temp_label {
                font-size: 13px;
            }
        """)

        self.get_weather_button.clicked.connect(self.get_weather)
        self.unit_toggle_button.clicked.connect(self.toggle_units)

    # ------------------------------------------------------------------
    # Units
    # ------------------------------------------------------------------

    def toggle_units(self):
        self.units = "imperial" if self.units == "metric" else "metric"
        self.unit_toggle_button.setText(self.unit_symbol())
        if self.last_city:
            self.get_weather(city_override=self.last_city)

    def unit_symbol(self):
        return "°F" if self.units == "imperial" else "°C"

    # ------------------------------------------------------------------
    # Current weather
    # ------------------------------------------------------------------

    def get_weather(self, city_override=None):
        # city_override is keyword-only in practice: Qt's `clicked` signal
        # passes a bool through as the first positional arg, but `False`
        # is falsy so it safely falls through to the input box below.
        city = city_override or self.city_input.text().strip()

        if not city:
            self.display_error("Please enter a city name")
            return

        self.last_city = city

        # immediate feedback before the (blocking) network calls fire
        self.temperature_label.setText("Loading...")
        self.icon_label.clear()
        self.description_label.setText("")
        self.description_label.setStyleSheet("")
        QApplication.processEvents()

        self.fetch_current_weather(city)
        self.fetch_forecast(city)

    def fetch_current_weather(self, city):
        url = (
            "https://api.openweathermap.org/data/2.5/weather"
            f"?q={city}&appid={self.api_key}&units={self.units}"
        )
        try:
            response = requests.get(url, timeout=10)
            data = response.json()

            if response.status_code == 200:
                self.display_weather(data)
            else:
                self.display_error(data.get("message", "City not found"))

        except requests.exceptions.RequestException as e:
            self.display_error(f"Network error: {e}")

    def display_error(self, message):
        self.temperature_label.setText("")
        self.icon_label.clear()
        self.description_label.setText(message)
        self.description_label.setStyleSheet("color: #ff6b6b;")
        self.clear_forecast()

    def display_weather(self, data):
        self.description_label.setStyleSheet("")

        temperature = data["main"]["temp"]
        weather_id = data["weather"][0]["id"]
        icon_code = data["weather"][0]["icon"]
        description = data["weather"][0]["description"]

        self.temperature_label.setText(f"{temperature:.0f}{self.unit_symbol()}")
        self.description_label.setText(description.capitalize())
        self.set_icon(self.icon_label, icon_code, weather_id, size=100)
        self.apply_theme(weather_id)

    # ------------------------------------------------------------------
    # 5-day forecast
    # ------------------------------------------------------------------

    def fetch_forecast(self, city):
        url = (
            "https://api.openweathermap.org/data/2.5/forecast"
            f"?q={city}&appid={self.api_key}&units={self.units}"
        )
        try:
            response = requests.get(url, timeout=10)
            data = response.json()

            if response.status_code == 200:
                daily = self.group_forecast_by_day(data["list"])
                self.display_forecast(daily)
            else:
                self.clear_forecast()

        except requests.exceptions.RequestException:
            # the current-weather error message already covers network
            # failures for the user; just leave the forecast row blank
            self.clear_forecast()

    @staticmethod
    def group_forecast_by_day(entries):
        """
        The forecast API returns readings in 3-hour steps (dt_txt like
        '2026-09-05 15:00:00'). Group them by calendar date, track the
        min/max temp per day, and pick the reading closest to noon to
        represent that day's condition/icon.
        """
        days = defaultdict(list)
        for entry in entries:
            date_str = entry["dt_txt"].split(" ")[0]
            days[date_str].append(entry)

        daily_summary = []
        for date_str, day_entries in days.items():
            temps = [e["main"]["temp"] for e in day_entries]

            def hour_distance_from_noon(e):
                hour = int(e["dt_txt"].split(" ")[1].split(":")[0])
                return abs(hour - 12)

            representative = min(day_entries, key=hour_distance_from_noon)
            weather_id = representative["weather"][0]["id"]
            icon_code = representative["weather"][0]["icon"]

            date_obj = datetime.strptime(date_str, "%Y-%m-%d")

            daily_summary.append({
                "label": date_obj.strftime("%a"),  # e.g. "Mon"
                "high": max(temps),
                "low": min(temps),
                "weather_id": weather_id,
                "icon_code": icon_code,
            })

        return daily_summary[:5]

    def display_forecast(self, daily_data):
        for i, card in enumerate(self.forecast_cards):
            if i < len(daily_data):
                day = daily_data[i]
                card["day"].setText(day["label"])
                self.set_icon(card["icon"], day["icon_code"], day["weather_id"], size=44)
                card["temp"].setText(f'{day["high"]:.0f}° / {day["low"]:.0f}°')
            else:
                card["day"].setText("")
                card["icon"].clear()
                card["temp"].setText("")

    def clear_forecast(self):
        for card in self.forecast_cards:
            card["day"].setText("")
            card["icon"].clear()
            card["temp"].setText("")

    # ------------------------------------------------------------------
    # Icons & theme
    # ------------------------------------------------------------------

    def set_icon(self, label, icon_code, weather_id, size):
        """Try to show OpenWeatherMap's real icon; fall back to emoji if
        the icon download fails (offline, blocked, slow connection, etc)."""
        pixmap = self.fetch_icon_pixmap(icon_code, size)
        if pixmap is not None:
            label.setPixmap(pixmap)
        else:
            label.setText(self.get_weather_emoji(weather_id))

    @staticmethod
    def fetch_icon_pixmap(icon_code, size):
        try:
            url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                return pixmap.scaled(
                    size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
        except requests.exceptions.RequestException:
            pass
        return None

    def apply_theme(self, weather_id):
        """Paint the window background with a gradient that reflects the
        current weather condition, via QPalette rather than the stylesheet
        (see the note above setStyleSheet for why)."""
        top_color, bottom_color = self.get_theme_colors(weather_id)

        gradient = QLinearGradient(0, 0, 0, 1)
        gradient.setCoordinateMode(QGradient.ObjectBoundingMode)
        gradient.setColorAt(0.0, QColor(top_color))
        gradient.setColorAt(1.0, QColor(bottom_color))

        palette = self.palette()
        palette.setBrush(QPalette.Window, gradient)
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    @staticmethod
    def get_theme_colors(weather_id):
        if 200 <= weather_id <= 232:
            return ("#414165", "#1c1c2b")      # thunderstorm
        elif 300 <= weather_id <= 321 or 500 <= weather_id <= 531:
            return ("#57708c", "#2c3e50")      # drizzle / rain
        elif 600 <= weather_id <= 622:
            return ("#7a8fa6", "#4c5f72")      # snow
        elif 701 <= weather_id <= 781:
            return ("#7d8fa0", "#4f5f6f")      # mist / fog / haze
        elif weather_id == 800:
            return ("#4facfe", "#1a6fb5")      # clear sky
        elif 801 <= weather_id <= 804:
            return ("#78909c", "#455a64")      # clouds
        else:
            return ("#6d7f92", "#3f4c5a")      # fallback

    @staticmethod
    def get_weather_emoji(weather_id):
        if 200 <= weather_id <= 232:
            return "⛈️"
        elif 300 <= weather_id <= 321:
            return "🌦️"
        elif 500 <= weather_id <= 531:
            return "🌧️"
        elif 600 <= weather_id <= 622:
            return "❄️"
        elif 701 <= weather_id <= 741:
            return "🌫️"
        elif weather_id == 762:
            return "🌋"
        elif weather_id == 771:
            return "💨"
        elif weather_id == 781:
            return "🌪️"
        elif weather_id == 800:
            return "☀️"
        elif 801 <= weather_id <= 804:
            return "☁️"
        else:
            return "❓"


if __name__ == "__main__":
    app = QApplication(sys.argv)
    weather_app = WeatherApp()
    weather_app.show()
    sys.exit(app.exec_())

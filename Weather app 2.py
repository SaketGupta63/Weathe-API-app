import sys
import requests
from datetime import datetime
from collections import defaultdict

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout
)
from PyQt5.QtCore import Qt


class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()
        self.api_key = "adf13248bd2af81b250ebc793c9458ff"

        # --- current weather widgets ---
        self.city_label = QLabel("Enter City:", self)
        self.city_input = QLineEdit(self)
        self.get_weather_button = QPushButton("Get Weather", self)
        self.temperature_label = QLabel(self)
        self.emoji_label = QLabel(self)
        self.description_label = QLabel(self)

        # --- forecast widgets: 5 day "cards" ---
        self.forecast_cards = []  # list of dicts: {day, emoji, temp}
        for _ in range(5):
            self.forecast_cards.append({
                "day": QLabel(self),
                "emoji": QLabel(self),
                "temp": QLabel(self),
            })

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Weather App")

        vbox = QVBoxLayout()
        vbox.addWidget(self.city_label)
        vbox.addWidget(self.city_input)
        vbox.addWidget(self.get_weather_button)
        vbox.addWidget(self.temperature_label)
        vbox.addWidget(self.emoji_label)
        vbox.addWidget(self.description_label)

        # forecast row, laid out horizontally, one column per day
        forecast_row = QHBoxLayout()
        for card in self.forecast_cards:
            day_col = QVBoxLayout()
            day_col.addWidget(card["day"])
            day_col.addWidget(card["emoji"])
            day_col.addWidget(card["temp"])
            forecast_row.addLayout(day_col)
        vbox.addLayout(forecast_row)

        self.setLayout(vbox)

        # --- alignment ---
        self.city_label.setAlignment(Qt.AlignCenter)
        self.city_input.setAlignment(Qt.AlignCenter)
        self.temperature_label.setAlignment(Qt.AlignCenter)
        self.emoji_label.setAlignment(Qt.AlignCenter)
        self.description_label.setAlignment(Qt.AlignCenter)
        for card in self.forecast_cards:
            card["day"].setAlignment(Qt.AlignCenter)
            card["emoji"].setAlignment(Qt.AlignCenter)
            card["temp"].setAlignment(Qt.AlignCenter)

        # --- object names for styling ---
        self.city_label.setObjectName("city_label")
        self.city_input.setObjectName("city_input")
        self.get_weather_button.setObjectName("get_weather_button")
        self.temperature_label.setObjectName("temperature_label")
        self.emoji_label.setObjectName("emoji_label")
        self.description_label.setObjectName("description_label")
        for card in self.forecast_cards:
            card["day"].setObjectName("forecast_day_label")
            card["emoji"].setObjectName("forecast_emoji_label")
            card["temp"].setObjectName("forecast_temp_label")

        self.setStyleSheet("""
            QLabel, QPushButton {
                font-family: Arial, sans-serif;
            }
            QLabel#city_label {
                font-size: 40px;
                font-style: italic;
            }
            QLineEdit {
                font-size: 16px;
            }
            QLineEdit#city_input {
                font-size: 40px;
            }
            QPushButton#get_weather_button {
                font-size: 30px;
                font-weight: bold;
            }
            QLabel#temperature_label {
                font-size: 69px;
                font-weight: bold;
            }
            QLabel#emoji_label {
                font-size: 69px;
                font-family: "Segoe UI Emoji", sans-serif;
            }
            QLabel#description_label {
                font-size: 50px;
                font-weight: bold;
            }
            QLabel#forecast_day_label {
                font-size: 16px;
                font-weight: bold;
            }
            QLabel#forecast_emoji_label {
                font-size: 32px;
                font-family: "Segoe UI Emoji", sans-serif;
            }
            QLabel#forecast_temp_label {
                font-size: 14px;
            }
        """)

        self.get_weather_button.clicked.connect(self.get_weather)

    # ------------------------------------------------------------------
    # Current weather
    # ------------------------------------------------------------------

    def get_weather(self):
        city = self.city_input.text().strip()

        if not city:
            self.display_error("Please enter a city name")
            return

        self.fetch_current_weather(city)
        self.fetch_forecast(city)

    def fetch_current_weather(self, city):
        url = (
            "https://api.openweathermap.org/data/2.5/weather"
            f"?q={city}&appid={self.api_key}&units=metric"
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
        self.emoji_label.setText("")
        self.description_label.setText(message)
        self.description_label.setStyleSheet("color: red;")
        self.clear_forecast()

    def display_weather(self, data):
        self.description_label.setStyleSheet("")

        temperature_c = data["main"]["temp"]
        weather_id = data["weather"][0]["id"]
        description = data["weather"][0]["description"]

        self.temperature_label.setText(f"{temperature_c:.0f}°C")
        self.description_label.setText(description.capitalize())
        self.emoji_label.setText(self.get_weather_emoji(weather_id))

    # ------------------------------------------------------------------
    # 5-day forecast
    # ------------------------------------------------------------------

    def fetch_forecast(self, city):
        url = (
            "https://api.openweathermap.org/data/2.5/forecast"
            f"?q={city}&appid={self.api_key}&units=metric"
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
            # Current-weather error message already covers network failures;
            # just leave the forecast row blank here.
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

            # pick the entry whose time is closest to 12:00 as "representative"
            def hour_distance_from_noon(e):
                hour = int(e["dt_txt"].split(" ")[1].split(":")[0])
                return abs(hour - 12)

            representative = min(day_entries, key=hour_distance_from_noon)
            weather_id = representative["weather"][0]["id"]

            date_obj = datetime.strptime(date_str, "%Y-%m-%d")

            daily_summary.append({
                "label": date_obj.strftime("%a"),   # e.g. "Mon"
                "high": max(temps),
                "low": min(temps),
                "weather_id": weather_id,
            })

        # keep chronological order, cap at 5 days
        return daily_summary[:5]

    def display_forecast(self, daily_data):
        for i, card in enumerate(self.forecast_cards):
            if i < len(daily_data):
                day = daily_data[i]
                card["day"].setText(day["label"])
                card["emoji"].setText(self.get_weather_emoji(day["weather_id"]))
                card["temp"].setText(f'{day["high"]:.0f}\u00b0 / {day["low"]:.0f}\u00b0')
            else:
                card["day"].setText("")
                card["emoji"].setText("")
                card["temp"].setText("")

    def clear_forecast(self):
        for card in self.forecast_cards:
            card["day"].setText("")
            card["emoji"].setText("")
            card["temp"].setText("")

    # ------------------------------------------------------------------
    # Shared
    # ------------------------------------------------------------------

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
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    weather_app = WeatherApp()
    weather_app.show()
    sys.exit(app.exec_())
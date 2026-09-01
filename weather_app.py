import sys
import requests
from PyQt5.QtWidgets import (QApplication, QLabel, QLineEdit, QPushButton,
                              QVBoxLayout, QWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class WeatherWorker(QThread):
    """
    Runs the network request on a separate thread so the GUI's event loop
    (and therefore the whole window) stays responsive while we wait on
    the API. Communicates results back to the main thread via signals --
    you should NEVER touch GUI widgets directly from inside a QThread.
    """
    success = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, city, api_key):
        super().__init__()
        self.city = city
        self.api_key = api_key

    def run(self):
        url = (
            "https://api.openweathermap.org/data/2.5/weather"
            f"?q={self.city}&appid={self.api_key}&units=metric"
        )
        try:
            response = requests.get(url, timeout=10)
            data = response.json()

            if response.status_code == 200:
                self.success.emit(data)
            else:
                self.error.emit(data.get("message", "City not found"))

        except requests.exceptions.RequestException as e:
            self.error.emit(f"Network error: {e}")


class WeatherApp(QWidget):
    def __init__(self):
        super().__init__()
        self.city_label = QLabel("Enter City:", self)
        self.city_input = QLineEdit(self)
        self.get_weather_button = QPushButton("Get Weather", self)
        self.temperature_label = QLabel(self)
        self.emoji_label = QLabel(self)
        self.description_label = QLabel(self)
        self.worker = None  # keep a reference so the thread isn't garbage-collected mid-run
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
        self.setLayout(vbox)

        self.city_label.setAlignment(Qt.AlignCenter)
        self.city_input.setAlignment(Qt.AlignCenter)
        self.temperature_label.setAlignment(Qt.AlignCenter)
        self.emoji_label.setAlignment(Qt.AlignCenter)
        self.description_label.setAlignment(Qt.AlignCenter)

        self.city_label.setObjectName("city_label")
        self.city_input.setObjectName("city_input")
        self.get_weather_button.setObjectName("get_weather_button")
        self.temperature_label.setObjectName("temperature_label")
        self.emoji_label.setObjectName("emoji_label")
        self.description_label.setObjectName("description_label")

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
        """)

        self.get_weather_button.clicked.connect(self.get_weather)

    def get_weather(self):
        city = self.city_input.text().strip()

        if not city:
            self.display_error("Please enter a city name")
            return

        api_key = "adf13248bd2af81b250ebc793c9458ff"

        # Give immediate feedback and prevent double-clicks while the
        # request is in flight -- this is only possible because the
        # request itself is no longer blocking the main thread.
        self.get_weather_button.setEnabled(False)
        self.get_weather_button.setText("Loading...")
        self.description_label.setStyleSheet("")
        self.description_label.setText("")
        self.temperature_label.setText("")
        self.emoji_label.setText("")

        self.worker = WeatherWorker(city, api_key)
        self.worker.success.connect(self.display_weather)
        self.worker.error.connect(self.display_error)
        self.worker.finished.connect(self.on_request_finished)
        self.worker.start()

    def on_request_finished(self):
        self.get_weather_button.setEnabled(True)
        self.get_weather_button.setText("Get Weather")

    def display_error(self, message):
        self.temperature_label.setText("")
        self.emoji_label.setText("")
        self.description_label.setText(message)
        self.description_label.setStyleSheet("color: red;")

    def display_weather(self, data):
        self.description_label.setStyleSheet("")

        temperature_c = data["main"]["temp"]
        weather_id = data["weather"][0]["id"]
        description = data["weather"][0]["description"]

        self.temperature_label.setText(f"{temperature_c:.0f}°C")
        self.description_label.setText(description.capitalize())
        self.emoji_label.setText(self.get_weather_emoji(weather_id))

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    weather_app = WeatherApp()
    weather_app.show()
    sys.exit(app.exec_())

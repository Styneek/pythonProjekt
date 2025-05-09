import json
from weatherData import WeatherData

class WeatherDataManager:
    def __init__(self, filepath):
        with open(filepath, encoding='utf-8') as f:
            self.weather = [WeatherData(data) for data in json.load(f)]

    def getForTrail(self, trailId):
        return [w for w in self.weather if w.trailId == trailId]

    def avgComfort(self, weatherList):
        if not weatherList:
            return 0
        return round(sum(w.comfortIndex() for w in weatherList) / len(weatherList), 1)

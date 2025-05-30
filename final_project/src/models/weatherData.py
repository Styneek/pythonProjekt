class WeatherData:
    def __init__(self, data):
        self.trailId = data.get("trail_id")
        self.date = data.get("date")
        self.locationId = data.get("location_id")
        self.avgTemp = float(data.get("avg_temp", 0))
        self.minTemp = float(data.get("min_temp", 0))
        self.maxTemp = float(data.get("max_temp", 0))
        self.precipitation = float(data.get("precipitation", 0))
        self.sunshineHours = float(data.get("sunshine_hours", 0))
        self.cloudCover = float(data.get("cloud_cover", 0))

    def isSunny(self, minHours=5):
        return self.sunshineHours >= minHours

    def isRainy(self, threshold=2.0):
        return self.precipitation > threshold

    def comfortIndex(self):
        tempScore = max(0, min(1, 1 - abs(22 - self.avgTemp) / 10))
        rainScore = max(0, 1 - self.precipitation / 10)
        cloudScore = max(0, 1 - self.cloudCover / 100)
        score = (tempScore * 0.4 + rainScore * 0.3 + cloudScore * 0.3) * 100
        return round(score, 1)

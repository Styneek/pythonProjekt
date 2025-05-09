class WeatherData:
    def __init__(self, data):
        self.trail_id = data.get('trail_id')
        self.avg_temp = float(data.get('avg_temp', 0))
        self.min_temp = float(data.get('min_temp', 0))
        self.max_temp = float(data.get('max_temp', 0))
        self.precipitation = float(data.get('precipitation', 0))
        self.sunshine_hours = float(data.get('sunshine_hours', 0))
        self.cloud_cover = float(data.get('cloud_cover', 0))

    @staticmethod
    def from_list(data_list):
        return [WeatherData(d) for d in data_list]

    @staticmethod
    def filter_by_trail(weather_list, trail_id):
        return [w for w in weather_list if w.trail_id == trail_id]

    @staticmethod
    def average_temperature(weather_list):
        temps = [w.avg_temp for w in weather_list]
        return sum(temps) / len(temps) if temps else 0

    @staticmethod
    def total_precipitation(weather_list):
        return sum(w.precipitation for w in weather_list)

    @staticmethod
    def sunny_days(weather_list, min_sun_hours):
        return sum(1 for w in weather_list if w.sunshine_hours >= min_sun_hours)

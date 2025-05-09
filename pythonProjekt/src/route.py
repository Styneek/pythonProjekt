class Route:
    def __init__(self, data):
        self.id = data.get('id')
        self.name = data.get('name')
        self.region = data.get('region')
        self.start_lat = float(data.get('start_lat', 0))
        self.start_lon = float(data.get('start_lon', 0))
        self.end_lat = float(data.get('end_lat', 0))
        self.end_lon = float(data.get('end_lon', 0))
        self.length_km = float(data.get('length_km', 0))
        self.elevation_gain = float(data.get('elevation_gain', 0))
        self.difficulty = int(data.get('difficulty', 1))
        self.terrain_type = data.get('terrain_type', '')
        self.tags = data.get('tags', '').split(',') if isinstance(data.get('tags'), str) else []

    def get_center(self):
        center_lat = (self.start_lat + self.end_lat) / 2
        center_lon = (self.start_lon + self.end_lon) / 2
        return center_lat, center_lon

    def estimate_time(self):
        base_speed = 4.0  
        uphill_penalty = self.elevation_gain / 600  
        difficulty_multiplier = {
            1: 1.0,
            2: 1.3,
            3: 1.6
        }.get(self.difficulty, 1.0)

        if self.terrain_type == 'mountain':
            terrain_multiplier = 1.5
        elif self.terrain_type == 'lakeside':
            terrain_multiplier = 1.0
        else:
            terrain_multiplier = 1.2

        hours = (self.length_km / base_speed) + uphill_penalty
        return round(hours * difficulty_multiplier * terrain_multiplier, 2)

    def matches_preferences(self, prefs):
        if prefs.region and self.region != prefs.region:
            return False
        if not (prefs.min_length <= self.length_km <= prefs.max_length):
            return False
        if prefs.difficulty and self.difficulty != prefs.difficulty:
            return False
        return True

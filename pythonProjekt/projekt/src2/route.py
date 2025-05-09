class Route:
    def __init__(self, data):
        self.id = data['id']
        self.name = data['name']
        self.region = data['region']
        self.lengthKm = float(data['length_km'])
        self.difficulty = int(data['difficulty'])
        tagsRaw = data.get('tags', "")
        self.tags = [tag.strip() for tag in tagsRaw.split(',')] if isinstance(tagsRaw, str) else tagsRaw
        self.elevationGain = float(data.get('elevation_gain', 0))
        self.terrainType = data.get('terrain_type', 'standard')
        self.startCoords = data.get('start_coords')
        self.endCoords = data.get('end_coords')

       


    def matchesPreference(self, preference):
        return (
            self.lengthKm <= preference.maxLength and
            self.difficulty <= preference.maxDifficulty
        )

    def estimateTimeHours(self):
        baseSpeed = 4
        elevationFactor = self.elevationGain / 600
        difficultyFactor = 1 + 0.2 * (self.difficulty - 1)
        return round(self.lengthKm / baseSpeed + elevationFactor * difficultyFactor, 2)

    def get_categories(self):
        categories = []

        if self.difficulty == 1 and self.lengthKm <= 8 and self.elevationGain <= 100:
            categories.append("Rodzinna")

        view_tags = ["view", "lake", "forest", "panorama"]
        if any(tag.strip().lower() in view_tags for tag in self.tags) or self.terrainType == "lakeside":
            categories.append("Widokowa")

        if self.difficulty >= 2 and self.lengthKm > 10:
            categories.append("Sportowa")

        if self.difficulty == 3 and self.elevationGain > 400:
            categories.append("Ekstremalna")

        return categories



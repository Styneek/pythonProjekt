from analyzers.review_analyzer import ReviewAnalyzer

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
        self.description = data.get('description', '')

        self.extractedInfo = {
            'time_estimate_minutes': None,
            'key_points': [],
            'warnings': [],
            'standardized_coords': {'start': None, 'end': None},
            'difficulty_text': None,
            'recommended_season': []
        }

        self.userReviews = data.get('reviews', [])
        self.reviewInsights = ReviewAnalyzer.analyze_reviews(self.userReviews) if self.userReviews else []


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

        if self.difficulty >= 2:
            categories.append("Wymagająca")
        
        if "mountain" in self.tags:
            categories.append("Górska")
        
        if "bike" in self.tags:
            categories.append("Rowerowa")

        if self.extractedInfo.get('difficulty_text') == 'trudna' or self.extractedInfo.get('difficulty_text') == 'bardzo trudna':
            if "Wymagająca" not in categories:
                categories.append("Wymagająca (z opisu)")
        if self.extractedInfo.get('warnings'):
            categories.append("Potencjalne_Zagrożenia")
        if self.extractedInfo.get('key_points'):
            categories.append("Atrakcje")

        return categories if categories else ["Ogólna"]
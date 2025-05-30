class RouteRecommender:
    def __init__(self, routeManager, weatherManager):
        self.routeManager = routeManager
        self.weatherManager = weatherManager

    def recommend(self, preference, region=None, selectedDate=None, weights=None):
        routes = self.routeManager.filterRoutes(preference, region)
        if not routes:
            return []

        recommendations = []
        for route in routes:
            
            weatherData = [
                w for w in self.weatherManager.getForTrail(route.id)
                if not selectedDate or w.date == selectedDate
            ]

            if not weatherData:
                avgTemp = 0
                sunnyDays = 0
                comfort = 0
            else:
                avgTemp = round(sum(w.avgTemp for w in weatherData) / len(weatherData), 1)
                sunnyDays = sum(w.isSunny(preference.sunHours) for w in weatherData)
                comfort = self.weatherManager.avgComfort(weatherData)

            categories = ", ".join(route.get_categories()) or "Brak"

            lengthScore = max(0, 100 - route.lengthKm * 5)         
            difficultyScore = max(0, 100 - route.difficulty * 30)  

            if weights:
                relevance = (
                    comfort * weights['weather'] +
                    lengthScore * weights['length'] +
                    difficultyScore * weights['difficulty']
                )
            else:
                relevance = comfort  

            recommendations.append({
                'route': route,
                'avgTemp': avgTemp,
                'sunnyDays': sunnyDays,
                'comfort': comfort,
                'categories': categories,
                'relevance': round(relevance, 1)
            })

      
        recommendations.sort(key=lambda r: -r['relevance'])
        return recommendations

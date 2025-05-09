from routeDataManager import RouteDataManager
from weatherDataManager import WeatherDataManager
from routeRecommender import RouteRecommender
from userInterface import UserInterface

def main():
    routeManager = RouteDataManager('data/routes/trails.json')
    weatherManager = WeatherDataManager('data/weather/weather.json')
    recommender = RouteRecommender(routeManager, weatherManager)

    region, selectedDate, preference, weights = UserInterface.getPreferences()
    recommendations = recommender.recommend(preference, region, selectedDate, weights)



    if not recommendations:
        print("Nie znaleziono dopasowanych tras.")
        return

    print("\nRekomendowane trasy:")
    with open("result.txt", "w", encoding="utf-8") as file:
        file.write("Rekomendowane trasy:\n")
        for r in recommendations[:5]:
            route = r['route']
            info = (
                f"\n{route.name} ({route.lengthKm} km, trudność {route.difficulty})\n"
                f" - Region: {route.region}\n"
                f" - Szacowany czas przejścia: {route.estimateTimeHours()} h\n"
                f" - Średnia temp.: {r['avgTemp']}°C\n"
                f" - Komfort od 0-100: {r['comfort']} / 100\n"
                f" - Kategorie trasy: {r['categories']}\n"
                f" - Ocena dopasowania: {r['relevance']} / 100\n"
        )
                    
        weatherData = [
            w for w in weatherManager.getForTrail(route.id)
            if w.date == selectedDate
        ]

        for w in weatherData:
            sunText = f" - {w.date} – słoneczny dzień!\n" if w.isSunny(preference.sunHours) else f" - {w.date} – pochmurno\n"
            info += sunText

        print(info)
        file.write(info)



    print("\nWyniki zapisane do pliku result.txt")


main()

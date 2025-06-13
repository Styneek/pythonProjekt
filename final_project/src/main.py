import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data_handlers.routeDataManager import RouteDataManager
from data_handlers.weatherDataManager import WeatherDataManager
from recommenders.routeRecommender import RouteRecommender
from ui.userInterface import UserInterface
from analyzers.text_processor import TextProcessor
from reporters.pdf_report_generator import PDFReportGenerator
from reporters.chart_generator import ChartGenerator
from extractors.html_route_extractor import HTMLRouteExtractor
from data.database.database_manager import DatabaseManager
from data.database.migration_tool import MigrationTool
from data.database.database_manager import DatabaseManager
from repositories.route_repository import RouteRepository
from repositories.weather_repository import WeatherRepository 
from repositories.user_repository import UserPreferenceRepository
from data.database.database_admin import DatabaseAdmin

def show_weather_for_trail():
    trail_id = int(input("ID trasy: "))
    db = DatabaseManager()
    repo = WeatherRepository(db)
    weather = repo.get_all_for_trail(trail_id)
    print(f"\n=== Pogoda dla trasy ID {trail_id} ===")
    for w in weather:
        print(f"{w[1]} | {w[2]} | Opady: {w[6]}mm | Temperatura: {w[7]}°C  | Zachmurzenie: {w[8]}%")

def add_trail():
            print("\n=== Dodawanie nowej trasy ===")
            name = input("Nazwa trasy: ")
            region = input("Region: ")
            start_lat = float(input("Start - szerokość (lat): "))
            start_lon = float(input("Start - długość (lon): "))
            end_lat = float(input("Koniec - szerokość (lat): "))
            end_lon = float(input("Koniec - długość (lon): "))
            length_km = float(input("Długość (km): "))
            elevation_gain = int(input("Przewyższenie (m): "))
            difficulty = int(input("Trudność (1-3): "))
            terrain_type = input("Typ terenu (np. forest, mountain): ")
            tags = input("Tagi (oddzielone przecinkiem): ")
            description = input("Opis trasy: ")

            route_data = {
                "name": name,
                "region": region,
                "start_lat": start_lat,
                "start_lon": start_lon,
                "end_lat": end_lat,
                "end_lon": end_lon,
                "length_km": length_km,
                "elevation_gain": elevation_gain,
                "difficulty": difficulty,
                "terrain_type": terrain_type,
                "tags": tags,
                "description": description
            }

            db = DatabaseManager()
            repo = RouteRepository(db)
            repo.add_route(route_data)

            print(f"\nTrasa '{name}' została dodana do bazy danych!")

def show_all_routes():
    db = DatabaseManager()
    repo = RouteRepository(db)
    routes = repo.get_all_routes()
    print("\n=== Lista tras w bazie ===")
    for route in routes:
        print(f"{route[1]} ({route[2]}) - {route[7]} km, trudność: {route[9]}")

def filter_routes():
    region = input("Region: ")
    max_length = float(input("Max długość (km): "))
    max_difficulty = int(input("Max trudność (1–3): "))

    db = DatabaseManager()
    repo = RouteRepository(db)

    class DummyPref: 
        def __init__(self, maxLength, maxDifficulty):
            self.maxLength = maxLength
            self.maxDifficulty = maxDifficulty

    filtered = repo.get_filtered_routes(region, DummyPref(max_length, max_difficulty))

    print("\n=== Wyniki filtrowania ===")
    for r in filtered:
        print(f"{r[0]}: {r[1]} ({r[2]}) - {r[7]} km, trudność: {r[9]}")

def handle_user_preferences():
    db = DatabaseManager()
    pref_repo = UserPreferenceRepository(db)

    region = input("Preferowany region: ")
    min_length = float(input("Minimalna długość trasy (km): "))
    max_length = float(input("Maksymalna długość trasy (km): "))
    max_difficulty = int(input("Maksymalna trudność (1–3): "))

    preferences = {
        "region": region,
        "min_length": min_length,
        "max_length": max_length,
        "max_difficulty": max_difficulty
    }

    pref_repo.save_preferences(preferences)
    print("\nPreferencje zostały zapisane!")

def database_menu():
    db = DatabaseManager()
    admin = DatabaseAdmin(db)

    while True:
        print("\n=== Admin Bazy Danych ===")
        print("1. Statystyki")
        print("2. Sprawdź integralność")
        print("3. Utwórz kopię zapasową")
        print("4. Wyczyść dane")
        print("0. Powrót")
        choice = input("Opcja: ")

        if choice == "1":
            admin.show_stats()
        elif choice == "2":
            admin.check_integrity()
        elif choice == "3":
            admin.backup_database()
        elif choice == "4":
            admin.clear_database()
        elif choice == "0":
            break
        else:
            print("Nieprawidłowy wybór.")

def main():
    with open("src/extractors/data.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    extractor = HTMLRouteExtractor(html_content)
    params = extractor.extract_route_params()
    reviews = extractor.extract_reviews()

    print("Parametry trasy:")
    print(params)

    print("\nRecenzje:")
    for review in reviews:
        print(f"- {review['rating']}: {review['text']}")

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

        pdf = PDFReportGenerator("reports/rekomendacje.pdf")
        pdf.add_title_page("Raport Rekomendacji Tras Turystycznych")

        route_names = []
        route_lengths = []
        route_relevances = []

        for r in recommendations[:5]:
            route = r['route']
            route_names.append(route.name)
            route_lengths.append(route.lengthKm)
            route_relevances.append(r['relevance'])

            route.extractedInfo = {}
            route.extractedInfo['time_estimate_minutes'] = TextProcessor.extract_time(route.description)
            route.extractedInfo['warnings'] = TextProcessor.extract_warnings(route.description)
            route.extractedInfo['gps'] = TextProcessor.extract_gps(route.description)
            route.extractedInfo['elevations'] = TextProcessor.extract_elevation(route.description)

            weatherData = [
                w for w in weatherManager.getForTrail(route.id)
                if w.date == selectedDate
            ]

            for w in weatherData:
                sunText = f" - {w.date} – słoneczny dzień!\n" if w.isSunny(preference.sunHours) else f" - {w.date} – pochmurno\n"

            pdf.add_route_details(route, route.extractedInfo)

        summary = (
            f"Analiza {len(recommendations)} tras.\n"
            f"Średnia długość: {round(sum(route_lengths) / len(route_lengths), 2)} km\n"
            f"Najwyższa ocena dopasowania: {max(route_relevances)} / 100"
        )
        pdf.add_summary_section(summary)

        chartGen = ChartGenerator()
        chartGen.bar_chart(route_lengths, route_names, "Długość tras (km)", "wykres_dlugosci.png")
        chartGen.bar_chart(route_relevances, route_names, "Ocena dopasowania tras", "wykres_ocen.png")
        
        pdf.add_section("Wykresy")
        pdf.add_image("reports/charts/wykres_dlugosci.png")
        pdf.add_image("reports/charts/wykres_ocen.png")
        
        pdf.add_section("Tabela porównawcza tras")
        pdf.add_table(
            headers=["Nazwa", "Region", "Długość (km)", "Trudność", "Dopasowanie"],
            data_rows=[
                [r['route'].name, r['route'].region, r['route'].lengthKm, r['route'].difficulty, r['relevance']]
                for r in recommendations
            ]
        )
        pdf.save()
        print("\nRaport PDF zapisany jako 'reports/rekomendacje.pdf'")
        # print("\nWyniki zapisane do pliku result.txt")

if __name__ == "__main__":
    db_manager = DatabaseManager()
    db_manager.initialize_database()
    print("Baza danych działa")

    migrator = MigrationTool(db_manager)
    migrator.migrate_routes_from_json("data/routes/trails.json")
    migrator.migrate_weather_from_json("data/weather/weather.json")

    while True:
        print("\n=== MENU ===")
        print("1. Dodaj trasę")
        print("2. Wyświetl pogodę dla trasy")
        print("3. Filtrowanie tras")
        print("4. Rekomendacje tras")
        print("5. Wyświetl wszystkie trasy")
        print("6. Ustaw preferencje użytkownika") 
        print("7. Admin Bazy Danych")
        print("0. Wyjście")
        choice = input("Wybierz opcję: ")

        if choice == "1":
            add_trail()
        elif choice == "2":
            show_weather_for_trail()
        elif choice == "3":
            filter_routes()
        elif choice == "4":
            main()
        elif choice == "5":
            show_all_routes()
        elif choice == "6":
            handle_user_preferences()
        elif choice == "7":
            database_menu()
        elif choice == "0":
            break
        else:
            print("Nieprawidłowy wybór.")

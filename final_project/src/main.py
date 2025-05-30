
from data_handlers.routeDataManager import RouteDataManager
from data_handlers.weatherDataManager import WeatherDataManager
from recommenders.routeRecommender import RouteRecommender
from ui.userInterface import UserInterface
from analyzers.text_processor import TextProcessor
from reporters.pdf_report_generator import PDFReportGenerator
from reporters.chart_generator import ChartGenerator

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
        print("\nWyniki zapisane do pliku result.txt")

main()

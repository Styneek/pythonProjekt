def generateOutput(trailsFound, weather, sunHours, averageTemperature, precipitation, sunnyDays):
    if not trailsFound:
        print("Nie znaleziono żadnych tras.")
        return ["Brak dopasowanych tras."]

    output = ["Rekomendowane trasy:"]

    for trail in trailsFound:
        weatherData = list(filter(lambda weatherInfo: weatherInfo['trail_id'] == trail['id'], weather))
        averageTemp = averageTemperature(weatherData)
        rain = precipitation(weatherData)
        sun = sunnyDays(weatherData, sunHours)

        output.append(f"\n{trail['name']} ({trail['length_km']} km, poziom trudności: {trail['difficulty']})")
        output.append(f"  - Region: {trail['region']}")
        output.append(f"  - Średnia temperatura: {averageTemp:.2f}°C")
        output.append(f"  - Opady: {rain:.1f} mm")
        output.append(f"  - Słoneczne dni: powyżej {sunHours}h słońca w conajmniej {sun} dniach")

    return output

def saveOutput(lines, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    print(f"\nWyniki zapisane do pliku '{filename}'")
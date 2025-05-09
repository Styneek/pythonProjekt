import json
from functools import reduce

def getFile(file):
    with open(file, 'r', encoding='utf-8') as fileName:
        return json.load(fileName)
    
def filterTrails(trails, min_length, max_length, difficulty, region):
    result = []
    for trail in trails:
        length = float(trail['length_km'])
        diff = int(trail['difficulty'])
        trail_region = trail['region']

        if length < min_length or length > max_length:
            continue
        if difficulty is not None and diff != difficulty:
            continue
        if region is not None and trail_region != region:
            continue

        result.append(trail)

    return result

def averageTemperature(data):
    temps = list(map(lambda tempInfo: float(tempInfo['avg_temp']), data))
    return reduce(lambda total, temp: total + temp, temps) / len(temps) if temps else 0

def precipitation(data):
    values = list(map(lambda valueInfo: float(valueInfo['precipitation']), data))
    return reduce(lambda total, temp: total + temp, values) if values else 0

def sunnyDays(data, sunMin):
    sunny = list(map(lambda sunnyInfo: float(sunnyInfo['sunshine_hours']) >= sunMin, data))
    return reduce(lambda total, temp: total + temp, sunny) if sunny else 0

trails = getFile('data/trails.json')
weather = getFile('data/weather.json')

region = input("Podaj region (Gdańsk, Gdynia, Sopot, Oliwa, Śródmieście, Rewa, Brzeźno, Sobieszewo, Przymorze): ").strip()
if not region:
    region = None
    
minLength = input("Podaj minimalną długość trasy (w km): ").strip()
minLength = float(minLength) if minLength else 0
maxLength = input("Podaj maksymalną długość trasy (w km): ").strip()
maxLength = float(maxLength) if maxLength else 100
difficulty = input("Podaj trudność trasy (od 1 do 3): ").strip()
difficulty = int(difficulty) if difficulty else None
sunHours = input("Godziny słoneczne (min): ").strip()
sunHours = float(sunHours) if sunHours else 0

trailsFound = filterTrails(trails, minLength, maxLength, difficulty, region)

if not trailsFound:
    print("Nie znaleźono trasy!!!")
    trailsFound = list(filter(lambda trail: trail['region'] == region, trails))[:3]

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

print("\n".join(output))

with open("result.txt", "w", encoding="utf-8") as file:
    file.write("\n".join(output))

print("\nWyniki zostały zapisane do pliku 'result.txt'")
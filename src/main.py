from dataLoader import getFile
from userInput import userPreference
from filterFile import filterTrails
from stats import averageTemperature, precipitation, sunnyDays
from report import generateOutput, saveOutput

def main():
    trails = getFile('data/trails.json')
    weather = getFile('data/weather.json')
    
    region, minLength, maxLength, difficulty, min_sun = userPreference()

    trailsFound = filterTrails(trails, minLength, maxLength, difficulty, region)

    if not trailsFound:
        print("Brak dokładnych dopasowań. Pokazuję alternatywy:")
      
        trailsFound = list(filter(lambda trail: trail['region'] == region, trails))[:3]

    linesOutput = generateOutput(trailsFound, weather, min_sun, averageTemperature, precipitation, sunnyDays)

    print("\n".join(linesOutput))
    saveOutput(linesOutput, "result.txt")


main()

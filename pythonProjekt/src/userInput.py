def userPreference():
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

    return region, minLength, maxLength, difficulty, sunHours
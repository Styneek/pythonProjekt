from userPreference import UserPreference

class UserInterface:
    @staticmethod
    def getPreferences():
        region = input("Podaj region (Przymorze, Oliwa, Śródmieście, Gdynia, Gdańsk, Sopot, Rewa, Brzeźno, Sobieszewo, ): ").strip() or None
        minLength = float(input("Minimalna długość trasy (w km): ") or 0)
        maxLength = float(input("Maksymalna długość trasy (w km): ") or 100)
        difficulty = int(input("Max trudność (1-3): ") or 3)
        # sunHours = float(input("Min. godziny słoneczne (w godzinach): ") or 0)
        selectedDate = input("Podaj datę od (2023-07-01) do (2023-07-07): ").strip()

       
        print("\nRozdziel 10 punktów, aby określić co jest dla Ciebie najważniejsze:")
        weatherPoints = int(input("Ile punktów dajesz pogodzie? (0–10): ") or 5)
        lengthPoints = int(input("Ile punktów dajesz długości trasy? (0–10): ") or 3)
        difficultyPoints = int(input("Ile punktów dajesz trudności trasy? (0–10): ") or 2)

        total = weatherPoints + lengthPoints + difficultyPoints
        if total != 10:
            print("Musisz rozdzielić dokładnie 10 punktów. Używam domyślnych wartości (5/3/2).")
            weatherPoints, lengthPoints, difficultyPoints = 5, 3, 2

       
        weights = {
            'weather': weatherPoints / 10,
            'length': lengthPoints / 10,
            'difficulty': difficultyPoints / 10
        }

        preference = UserPreference(maxLength, difficulty)
        return region, selectedDate, preference, weights

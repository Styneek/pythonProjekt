class UserPreference:
    def __init__(self, region=None, min_length=0, max_length=100, difficulty=None, sun_hours=0):
        self.region = region
        self.min_length = min_length
        self.max_length = max_length
        self.difficulty = difficulty
        self.sun_hours = sun_hours

    @staticmethod
    def from_input():
        region = input("Podaj region (np. Gdańsk, Gdynia): ").strip() or None

        try:
            min_length = float(input("Podaj minimalną długość trasy (km): ").strip())
        except:
            min_length = 0

        try:
            max_length = float(input("Podaj maksymalną długość trasy (km): ").strip())
        except:
            max_length = 100

        try:
            difficulty = int(input("Podaj trudność trasy (1-3): ").strip())
        except:
            difficulty = None

        try:
            sun_hours = float(input("Minimalne godziny słoneczne: ").strip())
        except:
            sun_hours = 0

        return UserPreference(region, min_length, max_length, difficulty, sun_hours)

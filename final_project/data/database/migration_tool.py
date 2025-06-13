import json
import os

class MigrationTool:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def migrate_routes_from_json(self, json_path):
        if not os.path.exists(json_path):
            print(f"Plik {json_path} nie istnieje.")
            return

        with open(json_path, 'r', encoding='utf-8') as file:
            try:
                routes = json.load(file)
            except Exception as e:
                print(f"Nie udało się wczytać JSON: {e}")
                return

        inserted = 0
        with self.db_manager.connect() as conn:
            cursor = conn.cursor()
            for route in routes:
                try:
                    cursor.execute("""
                        INSERT INTO routes (
                            name, region, start_lat, start_lon, end_lat, end_lon,
                            length_km, elevation_gain, difficulty, terrain_type,
                            tags, description
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        route["name"],
                        route["region"],
                        route["start_lat"],
                        route["start_lon"],
                        route["end_lat"],
                        route["end_lon"],
                        route["length_km"],
                        route["elevation_gain"],
                        route["difficulty"],
                        route["terrain_type"],
                        route["tags"], 
                        route["description"]
                    ))
                    inserted += 1
                except Exception as e:
                    print(f"[BŁĄD] Nie można dodać trasy: {route.get('name', 'brak nazwy')} -> {e}")
            conn.commit()
        print(f"Dodano {inserted} tras do bazy.")

    def migrate_weather_from_json(self, json_path):
        location_map = {
            "Oliwa": (54.4095, 18.5679),
            "Przymorze": (54.4149, 18.5911),
            "Śródmieście": (54.3520, 18.6466),
            "Gdynia": (54.5189, 18.5305),
            "Gdańsk": (54.3520, 18.6466),
            "Sopot": (54.4416, 18.5601),
            "Rewa": (54.6386, 18.5272),
            "Brzeźno": (54.4194, 18.6247),
            "Sobieszewo": (54.3175, 18.8784),
        }

        if not os.path.exists(json_path):
            print(f"Plik {json_path} nie istnieje.")
            return

        with open(json_path, 'r', encoding='utf-8') as file:
            try:
                weather_data = json.load(file)
            except Exception as e:
                print(f"Nie udało się wczytać JSON: {e}")
                return

        inserted = 0
        with self.db_manager.connect() as conn:
            cursor = conn.cursor()
            for record in weather_data:
                location_id = record.get("location_id")
                if location_id not in location_map:
                    print(f"Nieznana lokalizacja: {location_id}")
                    continue

                lat, lon = location_map[location_id]

                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO weather_data (
                            trail_id, date, location_lat, location_lon,
                            avg_temp, min_temp, max_temp, precipitation,
                            sunshine_hours, cloud_cover
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record["trail_id"],
                        record["date"],
                        lat,
                        lon,
                        record["avg_temp"],
                        record["min_temp"],
                        record["max_temp"],
                        record["precipitation"],
                        record["sunshine_hours"],
                        record["cloud_cover"]
                    ))
                    inserted += 1
                except Exception as e:
                    print(f"Nie można dodać danych pogodowych: {record.get('date')} -> {e}")
            conn.commit()
        print(f"Dodano {inserted} rekordów pogodowych do bazy.")


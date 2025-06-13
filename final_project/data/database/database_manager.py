import sqlite3

class DatabaseManager:
    def __init__(self, db_path="data/database/routes.db"):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path)

    def initialize_database(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.executescript("""
            CREATE TABLE IF NOT EXISTS routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                region TEXT,
                start_lat REAL NOT NULL,
                start_lon REAL NOT NULL,
                end_lat REAL NOT NULL,
                end_lon REAL NOT NULL,
                length_km REAL,
                elevation_gain INTEGER,
                difficulty INTEGER CHECK (difficulty BETWEEN 1 AND 5),
                terrain_type TEXT,
                tags TEXT,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

           CREATE TABLE IF NOT EXISTS weather_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trail_id INTEGER,
                date DATE NOT NULL,
                location_lat REAL NOT NULL,
                location_lon REAL NOT NULL,
                avg_temp REAL,
                min_temp REAL,
                max_temp REAL,
                precipitation REAL,
                sunshine_hours REAL,
                cloud_cover INTEGER,
                UNIQUE(trail_id, date)
            );


            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT DEFAULT 'default',
                preferred_temp_min REAL,
                preferred_temp_max REAL,
                max_precipitation REAL,
                max_difficulty INTEGER,
                max_length_km REAL,
                preferred_terrain_types TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_routes_region ON routes(region);
            CREATE INDEX IF NOT EXISTS idx_routes_difficulty ON routes(difficulty);
            CREATE INDEX IF NOT EXISTS idx_weather_date ON weather_data(date);
            """)
            conn.commit()

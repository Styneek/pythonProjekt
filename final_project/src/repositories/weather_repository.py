class WeatherRepository:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def add_weather_record(self, record):
        with self.db_manager.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO weather_data (
                    trail_id, date, location_id,
                    avg_temp, min_temp, max_temp,
                    precipitation, sunshine_hours, cloud_cover
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["trail_id"],
                record["date"],
                record["location_id"],
                record["avg_temp"],
                record["min_temp"],
                record["max_temp"],
                record["precipitation"],
                record["sunshine_hours"],
                record["cloud_cover"]
            ))
            conn.commit()

    def get_weather_by_trail_and_date(self, trail_id, date):
        with self.db_manager.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM weather_data
                WHERE trail_id = ? AND date = ?
            """, (trail_id, date))
            return cursor.fetchone()

    def get_all_for_trail(self, trail_id):
        with self.db_manager.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM weather_data
                WHERE trail_id = ?
            """, (trail_id,))
            return cursor.fetchall()

    # def get_weather_by_location_and_date(self, location_id, date):
    #     with self.db_manager.connect() as conn:
    #         cursor = conn.cursor()
    #         cursor.execute("""
    #             SELECT * FROM weather_data
    #             WHERE location_id = ? AND date = ?
    #         """, (location_id, date))
    #         return cursor.fetchone()

    def get_stats_for_trail(self, trail_id):
        with self.db_manager.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    AVG(avg_temp), MIN(min_temp), MAX(max_temp),
                    AVG(precipitation), AVG(sunshine_hours), AVG(cloud_cover)
                FROM weather_data
                WHERE trail_id = ?
            """, (trail_id,))
            result = cursor.fetchone()
            return {
                "avg_temp": result[0],
                "min_temp": result[1],
                "max_temp": result[2],
                "avg_precip": result[3],
                "avg_sun": result[4],
                "avg_cloud": result[5]
            }

    def delete_weather_for_trail(self, trail_id):
        with self.db_manager.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM weather_data WHERE trail_id = ?", (trail_id,))
            conn.commit()

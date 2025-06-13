class UserPreferenceRepository:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def save_preferences(self, prefs):
        with self.db_manager.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_preferences WHERE user_name = 'default'")
            cursor.execute("""
                INSERT INTO user_preferences (
                    user_name, max_difficulty, max_length_km,
                    preferred_terrain_types, preferred_temp_min,
                    preferred_temp_max, max_precipitation
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                'default',
                prefs.get("max_difficulty"),
                prefs.get("max_length"),
                '',  
                None, None, None  
            ))
            conn.commit()

    def get_preferences(self):
        with self.db_manager.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT max_difficulty, max_length_km
                FROM user_preferences
                WHERE user_name = 'default'
            """)
            result = cursor.fetchone()
            if result:
                return {
                    "max_difficulty": result[0],
                    "max_length": result[1]
                }
            return None

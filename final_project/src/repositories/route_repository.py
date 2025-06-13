import math

class RouteRepository:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_all_routes(self):
        with self.db_manager.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM routes")
            return cursor.fetchall()

    def find_by_region_and_difficulty(self, region, max_difficulty=5):
        with self.db_manager.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM routes
                WHERE region = ? AND difficulty <= ?
            """, (region, max_difficulty))
            return cursor.fetchall()

    def find_by_length(self, max_length_km):
        with self.db_manager.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM routes
                WHERE length_km <= ?
            """, (max_length_km,))
            return cursor.fetchall()

    # def find_by_tags(self, tag_fragment):
    #     with self.db_manager.connect() as conn:
    #         cursor = conn.cursor()
    #         cursor.execute("""
    #             SELECT * FROM routes
    #             WHERE tags LIKE ?
    #         """, (f"%{tag_fragment}%",))
    #         return cursor.fetchall()

    def add_route(self, route_dict):
        with self.db_manager.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO routes (
                    name, region, start_lat, start_lon, end_lat, end_lon,
                    length_km, elevation_gain, difficulty, terrain_type,
                    tags, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                route_dict["name"],
                route_dict["region"],
                route_dict["start_lat"],
                route_dict["start_lon"],
                route_dict["end_lat"],
                route_dict["end_lon"],
                route_dict["length_km"],
                route_dict["elevation_gain"],
                route_dict["difficulty"],
                route_dict["terrain_type"],
                route_dict["tags"],
                route_dict["description"]
            ))
            conn.commit()

    def update_route(self, route_id, updated_fields: dict):
        if not updated_fields:
            return
        set_clause = ", ".join([f"{key} = ?" for key in updated_fields.keys()])
        values = list(updated_fields.values())
        values.append(route_id)

        with self.db_manager.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE routes SET {set_clause}
                WHERE id = ?
            """, values)
            conn.commit()

    # def find_near_location(self, lat, lon, radius_km):
    #     def haversine(lat1, lon1, lat2, lon2):
    #         R = 6371
    #         dlat = math.radians(lat2 - lat1)
    #         dlon = math.radians(lon2 - lon1)
    #         a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * \
    #             math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    #         return R * 2 * math.asin(math.sqrt(a))

    #     with self.db_manager.connect() as conn:
    #         cursor = conn.cursor()
    #         cursor.execute("SELECT * FROM routes")
    #         rows = cursor.fetchall()

    #     nearby_routes = []
    #     for row in rows:
    #         start_lat, start_lon = row[3], row[4]
    #         distance = haversine(lat, lon, start_lat, start_lon)
    #         if distance <= radius_km:
    #             nearby_routes.append(row)

    #     return nearby_routes

    def get_filtered_routes(self, region, preference):
        with self.db_manager.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM routes
                WHERE region = ?
                AND length_km <= ?
                AND difficulty <= ?
            """, (
                region,
                preference.maxLength,
                preference.maxDifficulty
            ))
            return cursor.fetchall()

import os
import shutil
from datetime import datetime, timedelta

class DatabaseAdmin:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def show_stats(self):
        with self.db_manager.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM routes")
            route_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM weather_data")
            weather_count = cursor.fetchone()[0]

        print("\n=== Statystyki bazy danych ===")
        print(f"Liczba tras: {route_count}")
        print(f"Liczba rekordów pogodowych: {weather_count}")

    def check_integrity(self):
        with self.db_manager.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            result = cursor.fetchone()[0]
        print("\nSprawdzanie integralności bazy:")
        print("OK" if result == "ok" else f"Problemy: {result}")

    def backup_database(self, backup_path="data/database/backup_routes.db"):
        if not os.path.exists("data/database/routes.db"):
            print("Baza danych nie istnieje.")
            return

        shutil.copy("data/database/routes.db", backup_path)
        print(f"\nKopia zapasowa zapisana jako: {backup_path}")

    def clear_database(self):
        with self.db_manager.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM weather_data")
            cursor.execute("DELETE FROM routes")
            cursor.execute("DELETE FROM user_preferences")
            conn.commit()

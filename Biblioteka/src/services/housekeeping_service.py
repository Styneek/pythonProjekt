import logging
from src.models.housekeeping_task import HousekeepingTask
from src.data.data_manager import DataManager
from src.services.room_service import RoomService
from datetime import datetime, timedelta

logger = logging.getLogger('hotel_reservation_app')  

class HousekeepingService:
    def __init__(self, data_manager: DataManager, room_service: RoomService):
        self.data_manager = data_manager
        self.room_service = room_service
        self.tasks = self.data_manager.load_housekeeping_tasks()
        logger.info("HousekeepingService zainicjowany.")

    def _save_tasks(self):
        self.data_manager.save_housekeeping_tasks(self.tasks)
        logger.debug("Zapisano zadania sprzątania do pliku.")

    def create_task(self, room_number, assigned_to, due_date_str, notes=""):
        room = self.room_service.get_room(room_number)
        if not room:
            print(f"Błąd: Pokój {room_number} nie znaleziono. Nie można utworzyć zadania sprzątania.")
            logger.warning(f"Próba utworzenia zadania sprzątania dla nieistniejącego pokoju: {room_number}")
            return None
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError as e:
            print("Błąd: Nieprawidłowy format daty. Użyj RRRR-MM-DD.")
            logger.error(f"Błąd formatu daty podczas tworzenia zadania sprzątania: {due_date_str} - {e}")
            return None
        
        for task in self.tasks:
            if task.room_number == room_number and task.status in ["pending", "in_progress"]:
                print(f"Ostrzeżenie: Istnieje już aktywne zadanie sprzątania dla pokoju {room_number}. Nie tworzę nowego.")
                logger.warning(f"Istnieje już aktywne zadanie sprzątania dla pokoju {room_number}. Nie tworzę nowego.")
                return None 

        task_id = f"HKT{len(self.tasks) + 1:04d}"
        task = HousekeepingTask(task_id, room_number, assigned_to, due_date, notes=notes)
        self.tasks.append(task)
        self._save_tasks()
        print(f"Zadanie sprzątania {task_id} dla pokoju {room_number} zostało utworzone i przypisane do {assigned_to}. Termin: {due_date}.")
        logger.info(f"Utworzono zadanie sprzątania: {task_id} dla pokoju {room_number}, przypisane do {assigned_to}, termin: {due_date}.")
        return task

    def get_task(self, task_id):
        task = next((task for task in self.tasks if task.task_id == task_id), None)
        if task:
            logger.debug(f"Pobrano zadanie sprzątania: {task_id}")
        else:
            logger.debug(f"Nie znaleziono zadania sprzątania: {task_id}")
        return task

    def update_task_status(self, task_id, new_status, current_user_role, completed_date_str=None):
        task = self.get_task(task_id)
        if not task:
            print(f"Błąd: Zadanie sprzątania {task_id} nie znaleziono.")
            logger.warning(f"Próba aktualizacji statusu nieistniejącego zadania sprzątania: {task_id}")
            return False

        if new_status == "completed" and current_user_role not in ["pokojówka", "administrator"]:
            print(f"Błąd: Rola {current_user_role} nie ma uprawnień do oznaczania zadań jako ukończone.")
            logger.warning(f"Użytkownik z rolą {current_user_role} próbował ukończyć zadanie {task_id} bez uprawnień.")
            return False
        if new_status in ["in_progress", "pending", "cancelled"] and current_user_role not in ["pokojówka", "recepcjonista", "administrator"]:
             print(f"Błąd: Rola {current_user_role} nie ma uprawnień do zmiany statusu zadania na {new_status}.")
             logger.warning(f"Użytkownik z rolą {current_user_role} próbował zmienić status zadania {task_id} na {new_status} bez uprawnień.")
             return False

        completed_date = None
        if new_status == "completed" and not completed_date_str:
            completed_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif completed_date_str:
            try:
                completed_date = datetime.strptime(completed_date_str, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
            except ValueError as e:
                print("Błąd: Nieprawidłowy format daty ukończenia. Użyj RRRR-MM-DD GG:MM:SS.")
                logger.error(f"Błąd formatu daty ukończenia zadania {task_id}: {completed_date_str} - {e}")
                return False

        if task.update_status(new_status, completed_date):
            self._save_tasks()
            if new_status == "completed":
                room = self.room_service.get_room(task.room_number)
                if room and room.status == "cleaning":
                    self.room_service.update_room_status(room.number, "available")
                    print(f"Status pokoju {room.number} zaktualizowano na 'dostępny' po ukończeniu sprzątania.")
                    logger.info(f"Pokój {room.number} zaktualizowano na 'dostępny' po ukończeniu zadania sprzątania {task_id}.")
            print(f"Status zadania {task_id} zaktualizowano na '{new_status}'.")
            logger.info(f"Zaktualizowano status zadania sprzątania {task_id} na {new_status}.")
            return True
        else:
            print(f"Błąd: Nieprawidłowy status '{new_status}' dla zadania {task_id}. Możliwe stany: pending, in_progress, completed, cancelled.")
            logger.warning(f"Nieprawidłowy status {new_status} dla zadania sprzątania {task_id}")
            return False

    def assign_task(self, task_id, assigned_to):
        task = self.get_task(task_id)
        if task:
            task.assigned_to = assigned_to
            self._save_tasks()
            print(f"Zadanie {task_id} przypisano do {assigned_to} pomyślnie.")
            logger.info(f"Przypisano zadanie sprzątania {task_id} do {assigned_to}.")
            return True
        print(f"Błąd: Zadanie sprzątania {task_id} nie znaleziono.")
        logger.warning(f"Próba przypisania zadania sprzątania {task_id}, które nie istnieje.")
        return False

    def delete_task(self, task_id):
        original_len = len(self.tasks)
        self.tasks = [task for task in self.tasks if task.task_id != task_id]
        if len(self.tasks) < original_len:
            self._save_tasks()
            print(f"Zadanie sprzątania {task_id} zostało usunięte pomyślnie.")
            logger.info(f"Usunięto zadanie sprzątania: {task_id}")
            return True
        print(f"Błąd: Zadanie sprzątania {task_id} nie znaleziono.")
        logger.warning(f"Próba usunięcia zadania sprzątania {task_id}, które nie istnieje.")
        return False

    def list_all_tasks(self):
        if not self.tasks:
            print("Brak zadań sprzątania w systemie.")
            logger.info("Brak zadań sprzątania w systemie do wyświetlenia.")
            return []
        logger.info("Wyświetlono wszystkie zadania sprzątania.")
        return self.tasks

    def get_daily_schedule(self, date_str):
        try:
            schedule_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError as e:
            print("Błąd: Nieprawidłowy format daty. Użyj RRRR-MM-DD.")
            logger.error(f"Błąd formatu daty podczas generowania harmonogramu dziennego: {date_str} - {e}")
            return []

        daily_tasks = [task for task in self.tasks if datetime.strptime(task.due_date, "%Y-%m-%d").date() == schedule_date and task.status != "completed"]

        if not daily_tasks:
            print("Brak zaplanowanych zadań sprzątania na ten dzień.")
            logger.info(f"Brak zaplanowanych zadań sprzątania na {date_str}.")
        else:
            logger.info(f"Wygenerowano harmonogram sprzątania na {date_str}. Znaleziono {len(daily_tasks)} zadań.")
        return daily_tasks

if __name__ == "__main__":
    dm = DataManager()
    class MockRoomService:
        def get_room(self, room_number):
            if room_number == "101": return type("Room", (object,), {"number": "101", "status": "cleaning"})()
            if room_number == "102": return type("Room", (object,), {"number": "102", "status": "available"})()
            return None
        def update_room_status(self, room_number, new_status):
            print(f"MockRoomService: Status pokoju {room_number} zaktualizowany na {new_status}.")

    room_service = MockRoomService()
    housekeeping_service = HousekeepingService(dm, room_service)

    print("\n--- Testowanie Usług Sprzątania ---")
    housekeeping_service.create_task("101", "Ania", "2023-06-11", "Głębokie sprzątanie")
    housekeeping_service.create_task("102", "Tomek", "2023-06-11")
    housekeeping_service.create_task("103", "Basia", "2023-06-12")

    print("\nWszystkie zadania:")
    housekeeping_service.list_all_tasks()

    print("\nHarmonogram na 2023-06-11:")
    housekeeping_service.get_daily_schedule("2023-06-11")

    housekeeping_service.update_task_status("HKT001", "in_progress")
    print("\nZadanie HKT001 po aktualizacji statusu:")
    print(housekeeping_service.get_task("HKT001"))

    housekeeping_service.update_task_status("HKT001", "completed")
    print("\nZadanie HKT001 po zakończeniu:")
    print(housekeeping_service.get_task("HKT001"))

    housekeeping_service.assign_task("HKT002", "Zofia")
    print("\nZadanie HKT002 po przypisaniu:")
    print(housekeeping_service.get_task("HKT002")) 
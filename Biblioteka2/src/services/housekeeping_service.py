import logging
from src.models.housekeeping_task import HousekeepingTask
from datetime import datetime

logger = logging.getLogger('hotel_reservation_app')  

class HousekeepingService:
    def __init__(self, db_manager, room_service):
        self.db_manager = db_manager
        self.room_service = room_service
        logger.info("HousekeepingService zainicjowany (DB).")

    def create_task(self, room_number, assigned_to, due_date_str, notes=""):
        room = self.room_service.get_room(room_number)
        if not room:
            print(f"Błąd: Pokój {room_number} nie znaleziono. Nie można utworzyć zadania sprzątania.")
            logger.warning(f"Próba utworzenia zadania sprzątania dla nieistniejącego pokoju: {room_number}")
            return None
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
        except ValueError as e:
            print("Błąd: Nieprawidłowy format daty. Użyj RRRR-MM-DD.")
            logger.error(f"Błąd formatu daty podczas tworzenia zadania sprzątania: {due_date_str} - {e}")
            return None
        # Sprawdź czy istnieje aktywne zadanie dla pokoju
        for task in self.db_manager.get_all_housekeeping_tasks():
            if task.room_number == room_number and task.status in ["pending", "in_progress"]:
                print(f"Ostrzeżenie: Istnieje już aktywne zadanie sprzątania dla pokoju {room_number}. Nie tworzę nowego.")
                logger.warning(f"Istnieje już aktywne zadanie sprzątania dla pokoju {room_number}. Nie tworzę nowego.")
                return None 
        all_tasks = self.db_manager.get_all_housekeeping_tasks()
        # Generowanie task_id
        task_id = f"HKT{len(all_tasks) + 1:04d}"
        task_data = {
            "task_id": task_id,
            "room_number": room_number,
            "assigned_to": assigned_to,
            "due_date": due_date,
            "status": "pending",
            "completed_date": None,
            "notes": notes
        }
        task = self.db_manager.add_housekeeping_task(task_data)
        print(f"Zadanie sprzątania {task_id} dla pokoju {room_number} zostało utworzone i przypisane do {assigned_to}. Termin: {due_date_str}.")
        logger.info(f"Utworzono zadanie sprzątania: {task_id} dla pokoju {room_number}, przypisane do {assigned_to}, termin: {due_date_str}.")
        return task

    def get_task(self, task_id):
        task = self.db_manager.get_housekeeping_task(task_id)
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
        #tylko admin i pokojowka moga zaznacza za skonczone
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
            completed_date = datetime.now()
        elif completed_date_str:
            try:
                completed_date = datetime.strptime(completed_date_str, "%Y-%m-%d %H:%M:%S")
            except ValueError as e:
                print("Błąd: Nieprawidłowy format daty ukończenia. Użyj RRRR-MM-DD GG:MM:SS.")
                logger.error(f"Błąd formatu daty ukończenia zadania {task_id}: {completed_date_str} - {e}")
                return False
        valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
        if new_status not in valid_statuses:
            print(f"Błąd: Nieprawidłowy status '{new_status}' dla zadania {task_id}. Możliwe stany: {', '.join(valid_statuses)}.")
            logger.warning(f"Nieprawidłowy status {new_status} dla zadania sprzątania {task_id}")
            return False
        update_data = {"status": new_status}#tworze slownik z nowym statusem
        if new_status == "completed":
            update_data["completed_date"] = completed_date
        self.db_manager.update_housekeeping_task(task_id, update_data)#aktualizuje w bazie
        if new_status == "completed":
            room = self.room_service.get_room(task.room_number)
            if room and room.status == "cleaning":
                self.room_service.update_room_status(room.number, "available")
                print(f"Status pokoju {room.number} zaktualizowano na 'dostępny' po ukończeniu sprzątania.")
                logger.info(f"Pokój {room.number} zaktualizowano na 'dostępny' po ukończeniu zadania sprzątania {task_id}.")
        print(f"Status zadania {task_id} zaktualizowano na '{new_status}'.")
        logger.info(f"Zaktualizowano status zadania sprzątania {task_id} na {new_status}.")
        return True

    def assign_task(self, task_id, assigned_to):
        task = self.get_task(task_id)
        if task:
            self.db_manager.update_housekeeping_task(task_id, {"assigned_to": assigned_to})
            print(f"Zadanie {task_id} przypisano do {assigned_to} pomyślnie.")
            logger.info(f"Przypisano zadanie sprzątania {task_id} do {assigned_to}.")
            return True
        print(f"Błąd: Zadanie sprzątania {task_id} nie znaleziono.")
        logger.warning(f"Próba przypisania zadania sprzątania {task_id}, które nie istnieje.")
        return False

    def delete_task(self, task_id):
        result = self.db_manager.delete_housekeeping_task(task_id)
        if result:
            print(f"Zadanie sprzątania {task_id} zostało usunięte pomyślnie.")
            logger.info(f"Usunięto zadanie sprzątania: {task_id}")
            return True
        print(f"Błąd: Zadanie sprzątania {task_id} nie znaleziono.")
        logger.warning(f"Próba usunięcia zadania sprzątania {task_id}, które nie istnieje.")
        return False

    def list_all_tasks(self):
        tasks = self.db_manager.get_all_housekeeping_tasks()
        if not tasks:
            print("Brak zadań sprzątania w systemie.")
            logger.info("Brak zadań sprzątania w systemie do wyświetlenia.")
            return []
        logger.info("Wyświetlono wszystkie zadania sprzątania.")
        return tasks

    def get_daily_schedule(self, date_str):
        try:
            schedule_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError as e:
            print("Błąd: Nieprawidłowy format daty. Użyj RRRR-MM-DD.")
            logger.error(f"Błąd formatu daty podczas generowania harmonogramu dziennego: {date_str} - {e}")
            return []
        daily_tasks = [task for task in self.db_manager.get_all_housekeeping_tasks() if task.due_date.date() == schedule_date and task.status != "completed"]
        if not daily_tasks:
            print("Brak zaplanowanych zadań sprzątania na ten dzień.")
            logger.info(f"Brak zaplanowanych zadań sprzątania na {date_str}.")
        else:
            logger.info(f"Wygenerowano harmonogram sprzątania na {date_str}. Znaleziono {len(daily_tasks)} zadań.")
        return daily_tasks

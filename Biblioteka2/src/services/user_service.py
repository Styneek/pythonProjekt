import logging

logger = logging.getLogger('hotel_reservation_app') 

class UserService:
    def __init__(self, db_manager):
        self.db_manager = db_manager #tworzy polaczenie z baza
        logger.info("UserService zainicjowany (DB).")
        if not self.db_manager.get_all_users():#sprawdza czy jest jakis user/ jak nie to tworzy admina
            print("Tworzenie domyślnego użytkownika administratora: admin/adminpass")
            self.add_user("admin", "adminpass", "administrator", "EMP000")
            logger.info("Domyślny użytkownik administratora został utworzony.")

    def add_user(self, username, password, role="recepcjonista", employee_id=None):
        if self.db_manager.get_user(username): # jezeli isteniej o takiej nazwie, Pass
            print(f"Błąd: Użytkownik o nazwie '{username}' już istnieje.")
            logger.warning(f"Próba dodania istniejącego użytkownika: {username}")
            return None
        user_data = {
            "username": username,
            "password": password,
            "role": role,
            "employee_id": employee_id
        }
        user = self.db_manager.add_user(user_data) #przekazuje slownik do databasemaneger i zapisuje usera
        print(f"Użytkownik '{username}' ({role.capitalize()}) został dodany pomyślnie.")
        logger.info(f"Dodano użytkownika: {username} z rolą {role}.")
        return user

    def authenticate_user(self, username, password):
        user = self.db_manager.get_user(username) #sprawdzaam czy istnieje
        if user and user.password == password:
            print(f"Użytkownik '{username}' zalogował się pomyślnie jako {user.role.capitalize()}.")
            logger.info(f"Użytkownik {username} pomyślnie uwierzytelniony jako {user.role}.")
            return user
        print("Błąd logowania: Nieprawidłowa nazwa użytkownika lub hasło.")
        logger.warning(f"Nieudana próba uwierzytelnienia dla użytkownika: {username}")
        return None

    def get_user_by_username(self, username):
        user = self.db_manager.get_user(username)
        if user:
            logger.debug(f"Pobrano użytkownika: {username}")
        else:
            logger.debug(f"Nie znaleziono użytkownika: {username}")
        return user

    def update_user(self, username, **kwargs): #kwargs dowolna liczba dodatkowych argumentow do aktualizacji k/v
        user = self.get_user_by_username(username)
        if user:
            update_data = {}
            for key, value in kwargs.items():
                if key == "password":
                    update_data[key] = value
                    logger.info(f"Zaktualizowano hasło użytkownika: {username}")
                elif key == "role":
                    valid_roles = ["administrator", "recepcjonista", "pokojówka"]
                    if value in valid_roles:
                        update_data[key] = value
                        logger.info(f"Zmieniono rolę użytkownika {username} na {value}.")
                    else:
                        print(f"Ostrzeżenie: Nieprawidłowa rola '{value}'. Rola użytkownika nie została zaktualizowana.")
                        logger.warning(f"Nieprawidłowa rola {value} podczas aktualizacji użytkownika {username}.")
                else:
                    update_data[key] = value
            self.db_manager.update_user(username, update_data)
            print(f"Użytkownik '{username}' został zaktualizowany pomyślnie.")
            logger.info(f"Zaktualizowano użytkownika: {username} z danymi: {kwargs}")
            return self.get_user_by_username(username)
        print(f"Błąd: Użytkownik '{username}' nie znaleziono.")
        logger.warning(f"Próba aktualizacji nieistniejącego użytkownika: {username}")
        return None

    def delete_user(self, username):
        result = self.db_manager.delete_user(username) # sprawdzam czy istnieje
        if result:
            print(f"Użytkownik '{username}' został usunięty pomyślnie.")
            logger.info(f"Usunięto użytkownika: {username}")
            return True
        print(f"Błąd: Użytkownik '{username}' nie znaleziono.")
        logger.warning(f"Próba usunięcia nieistniejącego użytkownika: {username}")
        return False

    def list_all_users(self):
        users = self.db_manager.get_all_users()
        if not users:
            print("Brak użytkowników w systemie.")
            logger.info("Brak użytkowników w systemie do wyświetlenia.")
            return []
        logger.info("Wyświetlono wszystkich użytkowników.")
        return users

    # def update_user_role(self, username, new_role):
    #     user = self.get_user_by_username(username)
    #     if not user:
    #         print(f"Błąd: Użytkownik '{username}' nie znaleziono.")
    #         logger.warning(f"Próba zmiany roli nieistniejącego użytkownika: {username}")
    #         return False
    #     valid_roles = ["administrator", "recepcjonista", "pokojówka"]
    #     if new_role not in valid_roles:
    #         print(f"Błąd: Nieprawidłowa rola '{new_role}'. Dostępne role: {valid_roles}")
    #         logger.warning(f"Nieprawidłowa rola {new_role} dla użytkownika {username}. Dostępne: {valid_roles}")
    #         return False
    #     old_role = user.role
    #     self.db_manager.update_user(username, {"role": new_role})
    #     print(f"Rola użytkownika '{username}' zmieniona z '{old_role}' na '{new_role}'.")
    #     logger.info(f"Zmieniono rolę użytkownika {username} z {old_role} na {new_role}.")
    #     return True
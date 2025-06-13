import logging
from src.models.user import User
from src.data.data_manager import DataManager

logger = logging.getLogger('hotel_reservation_app') 

class UserService:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.users = self.data_manager.load_users()
        logger.info("UserService zainicjowany.")
        if not self.users:
            print("Tworzenie domyślnego użytkownika administratora: admin/adminpass")
            self.add_user("admin", "adminpass", "administrator", "EMP000")
            self.users = self.data_manager.load_users() 
            logger.info("Domyślny użytkownik administratora został utworzony.")

    def _save_users(self):
        self.data_manager.save_users(self.users)
        logger.debug("Zapisano użytkowników do pliku.")

    def add_user(self, username, password, role="recepcjonista", employee_id=None):
        if any(user.username == username for user in self.users):
            print(f"Błąd: Użytkownik o nazwie '{username}' już istnieje.")
            logger.warning(f"Próba dodania istniejącego użytkownika: {username}")
            return None
        
        user = User(username, password, role, employee_id)
        self.users.append(user)
        self._save_users()
        print(f"Użytkownik '{username}' ({role.capitalize()}) został dodany pomyślnie.")
        logger.info(f"Dodano użytkownika: {username} z rolą {role}.")
        return user

    def authenticate_user(self, username, password):
        user = next((u for u in self.users if u.username == username), None)
        if user and user.password == password:  
            print(f"Użytkownik '{username}' zalogował się pomyślnie jako {user.role.capitalize()}.")
            logger.info(f"Użytkownik {username} pomyślnie uwierzytelniony jako {user.role}.")
            return user
        print("Błąd logowania: Nieprawidłowa nazwa użytkownika lub hasło.")
        logger.warning(f"Nieudana próba uwierzytelnienia dla użytkownika: {username}")
        return None

    def get_user_by_username(self, username):
        user = next((user for user in self.users if user.username == username), None)
        if user:
            logger.debug(f"Pobrano użytkownika: {username}")
        else:
            logger.debug(f"Nie znaleziono użytkownika: {username}")
        return user

    def update_user(self, username, **kwargs):
        user = self.get_user_by_username(username)
        if user:
            for key, value in kwargs.items():
                if key == "password": 
                    setattr(user, key, value)
                    logger.info(f"Zaktualizowano hasło użytkownika: {username}")
                elif key == "role": 
                    valid_roles = ["administrator", "recepcjonista", "pokojówka"]
                    if value in valid_roles:
                        setattr(user, key, value)
                        logger.info(f"Zmieniono rolę użytkownika {username} na {value}.")
                    else:
                        print(f"Ostrzeżenie: Nieprawidłowa rola '{value}'. Rola użytkownika nie została zaktualizowana.")
                        logger.warning(f"Nieprawidłowa rola {value} podczas aktualizacji użytkownika {username}.")
                else:
                    setattr(user, key, value)
            self._save_users()
            print(f"Użytkownik '{username}' został zaktualizowany pomyślnie.")
            logger.info(f"Zaktualizowano użytkownika: {username} z danymi: {kwargs}")
            return user
        print(f"Błąd: Użytkownik '{username}' nie znaleziono.")
        logger.warning(f"Próba aktualizacji nieistniejącego użytkownika: {username}")
        return None

    def delete_user(self, username):
        original_len = len(self.users)
        self.users = [user for user in self.users if user.username != username]
        if len(self.users) < original_len:
            self._save_users()
            print(f"Użytkownik '{username}' został usunięty pomyślnie.")
            logger.info(f"Usunięto użytkownika: {username}")
            return True
        print(f"Błąd: Użytkownik '{username}' nie znaleziono.")
        logger.warning(f"Próba usunięcia nieistniejącego użytkownika: {username}")
        return False

    def list_all_users(self):
        if not self.users:
            print("Brak użytkowników w systemie.")
            logger.info("Brak użytkowników w systemie do wyświetlenia.")
            return []
        logger.info("Wyświetlono wszystkich użytkowników.")
        return self.users

    def update_user_role(self, username, new_role):
        user = self.get_user_by_username(username)
        if not user:
            print(f"Błąd: Użytkownik '{username}' nie znaleziono.")
            logger.warning(f"Próba zmiany roli nieistniejącego użytkownika: {username}")
            return False
        
        valid_roles = ["administrator", "recepcjonista", "pokojówka"]
        if new_role not in valid_roles:
            print(f"Błąd: Nieprawidłowa rola '{new_role}'. Dostępne role: {valid_roles}")
            logger.warning(f"Nieprawidłowa rola {new_role} dla użytkownika {username}. Dostępne: {valid_roles}")
            return False

        old_role = user.role
        user.role = new_role
        self._save_users()
        print(f"Rola użytkownika '{username}' zmieniona z '{old_role}' na '{new_role}'.")
        logger.info(f"Zmieniono rolę użytkownika {username} z {old_role} na {new_role}.")
        return True

if __name__ == "__main__":
    dm = DataManager()
    user_service = UserService(dm)

    print("\n--- Testowanie Usługi Użytkowników ---")
    user_service.add_user("testuser", "testpass", "recepcjonista", "EMP002")
    user_service.add_user("housekeeper", "hkpass", "pokojówka")

    print("\nWszyscy użytkownicy po dodaniu:")
    user_service.list_all_users()

    authenticated_user = user_service.authenticate_user("admin", "adminpass")
    if authenticated_user: print(f"Zalogowany użytkownik: {authenticated_user.username}")

    user_service.update_user("testuser", role="administrator")
    print("\nUżytkownik 'testuser' po aktualizacji roli:")
    print(user_service.get_user_by_username("testuser"))

    user_service.delete_user("housekeeper")
    print("\nWszyscy użytkownicy po usunięciu:")
    user_service.list_all_users()

    user_service.authenticate_user("nonexistent", "pass")
    user_service.authenticate_user("admin", "wrongpass") 
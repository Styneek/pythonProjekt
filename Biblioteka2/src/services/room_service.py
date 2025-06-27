import logging
from src.database.db_manager import DatabaseManager
from src.database.models import Room

logger = logging.getLogger('hotel_reservation_app')

class RoomService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager #tworzy polaczenie z baza
        logger.info("RoomService zainicjowany (DB).")

    def add_room(self, number, floor, room_type, price, amenities=None):
        room_data = {
            "number": number,
            "floor": floor,
            "room_type": room_type,
            "price": price,
            "amenities": amenities or [],
            "status": "dostępny"
        }
        room = self.db_manager.add_room(room_data) # przekazuje dane do databasemanager
        if room:
            print(f"Pokój {number} został dodany pomyślnie.")
            logger.info(f"Dodano pokój: {number}")
        else:
            print(f"Błąd: Pokój o numerze {number} już istnieje.")
            logger.warning(f"Próba dodania istniejącego pokoju: {number}")
        return room

    def get_room(self, room_number):
        room = self.db_manager.get_room(room_number) # pobieram pokoj o numerze
        if room:
            logger.debug(f"Pobrano pokój: {room_number}")
        else:
            logger.debug(f"Nie znaleziono pokoju: {room_number}")
        return room

    def update_room(self, room_number, **kwargs): #kwargs dodwolna ilosc pol do aktualizacji k/v
        room = self.db_manager.update_room(room_number, kwargs) #wywolanie metody przekazujac numer/dane do aktualizacji
        if room:
            print(f"Pokój {room_number} został zaktualizowany pomyślnie.")
            logger.info(f"Zaktualizowano pokój: {room_number} z danymi: {kwargs}")
        else:
            print(f"Błąd: Pokój {room_number} nie znaleziono.")
            logger.warning(f"Próba aktualizacji nieistniejącego pokoju: {room_number}")
        return room

    def delete_room(self, room_number):
        room = self.db_manager.get_room(room_number) # sprawdzam czy istnieje
        if room:
            self.db_manager.db.delete(room)
            self.db_manager.db.commit()
            print(f"Pokój {room_number} został usunięty pomyślnie.")
            logger.info(f"Usunięto pokój: {room_number}")
            return True
        print(f"Błąd: Pokój {room_number} nie znaleziono.")
        logger.warning(f"Próba usunięcia nieistniejącego pokoju: {room_number}")
        return False

    def update_room_status(self, room_number, new_status):
        room = self.db_manager.get_room(room_number) # sprawdzam czy istnieje
        if room:
            room.status = new_status
            self.db_manager.db.commit()
            print(f"Status dla Pokoju {room_number} zmieniony na {new_status}.")
            logger.info(f"Zmieniono status pokoju {room_number} na {new_status}")
            return True
        else:
            print(f"Błąd: Pokój {room_number} nie znaleziono.")
            logger.warning(f"Próba zmiany statusu nieistniejącego pokoju: {room_number}")
        return False

    def list_all_rooms(self):
        rooms = self.db_manager.get_all_rooms() # pobiera wszystkie rekordy z tabeli pokoi 
        if not rooms:
            print("Brak pokoi w systemie.")
            logger.info("Brak pokoi w systemie do wyświetlenia.")
            return []
        logger.info("Wyświetlono wszystkie pokoje.")
        return rooms

    def find_available_rooms(self):
        rooms = self.db_manager.get_all_rooms()# pobiera wszystkie rekordy z tabeli pokoi
        available_rooms = [room for room in rooms if room.status == "dostępny"]#dla kazdego room w rooms czy status jest dostepny
        if not available_rooms:
            print("Brak dostępnych pokoi.")
            logger.info("Brak dostępnych pokoi do znalezienia.")
        else:
            logger.info(f"Znaleziono {len(available_rooms)} dostępnych pokoi.")
        return available_rooms

    def find_rooms_by_type(self, room_type):
        rooms = self.db_manager.get_all_rooms()#pobiera wszystkie pokoje
        filtered_rooms = [room for room in rooms if room.room_type and room.room_type.lower() == room_type.lower()]#tworze tzw List comprehension nowa lista zawierajaca tylko pokoje spelniajace warunek
        if not filtered_rooms:
            print(f"Brak pokoi typu '{room_type}'.")
            logger.info(f"Brak pokoi typu {room_type} do znalezienia.")
        else:
            logger.info(f"Znaleziono {len(filtered_rooms)} pokoi typu {room_type}.")
        return filtered_rooms

    def find_rooms_by_price_range(self, min_price, max_price):
        rooms = self.db_manager.get_all_rooms()#pobieram pokoje
        filtered_rooms = [room for room in rooms if min_price <= room.price <= max_price]#sprawdzam czy cena miesci sie w przedziale znowu list comprehension
        if not filtered_rooms:
            print(f"Brak pokoi w zakresie cenowym {min_price:.2f}-{max_price:.2f} PLN.")
            logger.info(f"Brak pokoi w zakresie cenowym {min_price}-{max_price} do znalezienia.")
        else:
            logger.info(f"Znaleziono {len(filtered_rooms)} pokoi w zakresie cenowym {min_price}-{max_price}.")
        return filtered_rooms

    def find_rooms_by_amenity(self, amenity):
        rooms = self.db_manager.get_all_rooms()#pobieram pokoje
        filtered_rooms = [room for room in rooms if room.amenities and amenity.lower() in [a.lower() for a in room.amenities]]#sprawdzma czy nie puste/ jak pasuje to dodaje
        if not filtered_rooms:
            print(f"Brak pokoi z udogodnieniem '{amenity}'.")
            logger.info(f"Brak pokoi z udogodnieniem {amenity} do znalezienia.")
        else:
            logger.info(f"Znaleziono {len(filtered_rooms)} pokoi z udogodnieniem {amenity}.")
        return filtered_rooms

    def search_rooms(self, room_type=None, min_price=None, max_price=None, amenity=None, status=None):
        rooms = self.db_manager.get_all_rooms()#pobieram pokoje
        results = rooms #lista robocza nakladam filtry
        if room_type:
            results = [room for room in results if room.room_type and room.room_type.lower() == room_type.lower()]
        if min_price is not None:
            results = [room for room in results if room.price >= min_price]
        if max_price is not None:
            results = [room for room in results if room.price <= max_price]
        if amenity:
            results = [room for room in results if room.amenities and amenity.lower() in [a.lower() for a in room.amenities]]
        if status:
            results = [room for room in results if room.status and room.status.lower() == status.lower()]
        if not results:
            print("Brak pokoi spełniających podane kryteria.")
            logger.info(f"Brak pokoi spełniających kryteria wyszukiwania (typ: {room_type}, cena: {min_price}-{max_price}, udogodnienie: {amenity}, status: {status}).")
        else:
            logger.info(f"Znaleziono {len(results)} pokoi spełniających kryteria wyszukiwania (typ: {room_type}, cena: {min_price}-{max_price}, udogodnienie: {amenity}, status: {status}).")
        return results

    def sort_rooms(self, rooms_list, sort_by, reverse=False):
        if not rooms_list:
            print("Brak pokoi do posortowania.")
            logger.info("Brak pokoi do posortowania.")
            return []
        valid_keys = ["number", "floor", "room_type", "price", "status"]
        if sort_by not in valid_keys:
            print(f"Błąd: Nieprawidłowe kryterium sortowania dla pokoi: {sort_by}. Dostępne: {', '.join(valid_keys)}.")
            logger.warning(f"Nieprawidłowe kryterium sortowania pokoi: {sort_by}")
            return rooms_list
        try:
            if sort_by in ["number", "room_type", "status"]:
                sorted_list = sorted(rooms_list, key=lambda room: getattr(room, sort_by).lower(), reverse=reverse)#getattr pobiera wartosc wskazanego atrybutu obiektu room/lambda zwraca dla kazdego pokoju wartosc po ktorej sortuje
            else:
                sorted_list = sorted(rooms_list, key=lambda room: getattr(room, sort_by), reverse=reverse)
            logger.info(f"Posortowano pokoje według {sort_by} (odwrócone: {reverse}).")
            return sorted_list
        except AttributeError as e:
            print(f"Błąd: Nie można posortować pokoi według atrybutu '{sort_by}'.")
            logger.error(f"Błąd atrybutu podczas sortowania pokoi ({sort_by}): {e}")
            return rooms_list


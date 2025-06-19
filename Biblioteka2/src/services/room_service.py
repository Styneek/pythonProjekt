import logging
from src.models.room import Room
from src.data.data_manager import DataManager

logger = logging.getLogger('hotel_reservation_app') 

class RoomService:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.rooms = self.data_manager.load_rooms()
        logger.info("RoomService zainicjowany.")

    def add_room(self, number, floor, room_type, price, amenities=None):
        if any(room.number == number for room in self.rooms):
            print(f"Błąd: Pokój o numerze {number} już istnieje.")
            logger.warning(f"Próba dodania istniejącego pokoju: {number}")
            return None
        room = Room(number, floor, room_type, price, amenities)
        self.rooms.append(room)
        self.data_manager.save_rooms(self.rooms)
        print(f"Pokój {number} został dodany pomyślnie.")
        logger.info(f"Dodano pokój: {number}")
        return room

    def get_room(self, room_number):
        room = next((room for room in self.rooms if room.number == room_number), None)
        if room:
            logger.debug(f"Pobrano pokój: {room_number}")
        else:
            logger.debug(f"Nie znaleziono pokoju: {room_number}")
        return room

    def update_room(self, room_number, **kwargs):
        room = self.get_room(room_number)
        if room:
            for key, value in kwargs.items():
                setattr(room, key, value)
            self.data_manager.save_rooms(self.rooms)
            print(f"Pokój {room_number} został zaktualizowany pomyślnie.")
            logger.info(f"Zaktualizowano pokój: {room_number} z danymi: {kwargs}")
            return room
        print(f"Błąd: Pokój {room_number} nie znaleziono.")
        logger.warning(f"Próba aktualizacji nieistniejącego pokoju: {room_number}")
        return None

    def delete_room(self, room_number):
        original_len = len(self.rooms)
        self.rooms = [room for room in self.rooms if room.number != room_number]
        if len(self.rooms) < original_len:
            self.data_manager.save_rooms(self.rooms)
            print(f"Pokój {room_number} został usunięty pomyślnie.")
            logger.info(f"Usunięto pokój: {room_number}")
            return True
        print(f"Błąd: Pokój {room_number} nie znaleziono.")
        logger.warning(f"Próba usunięcia nieistniejącego pokoju: {room_number}")
        return False

    def update_room_status(self, room_number, new_status):
        room = self.get_room(room_number)
        if room:
            if room.update_status(new_status):
                self.data_manager.save_rooms(self.rooms)
                print(f"Status dla Pokoju {room_number} zmieniony na {new_status}.")
                logger.info(f"Zmieniono status pokoju {room_number} na {new_status}")
                return True
            else:
                print(f"Błąd: Nieprawidłowy status '{new_status}'.")
                logger.warning(f"Nieprawidłowy status {new_status} dla pokoju {room_number}")
        else:
            print(f"Błąd: Pokój {room_number} nie znaleziono.")
            logger.warning(f"Próba zmiany statusu nieistniejącego pokoju: {room_number}")
        return False

    def list_all_rooms(self):
        if not self.rooms:
            print("Brak pokoi w systemie.")
            logger.info("Brak pokoi w systemie do wyświetlenia.")
            return []
        logger.info("Wyświetlono wszystkie pokoje.")
        return self.rooms

    def find_available_rooms(self):
        available_rooms = [room for room in self.rooms if room.status == "dostępny"]
        if not available_rooms:
            print("Brak dostępnych pokoi.")
            logger.info("Brak dostępnych pokoi do znalezienia.")
        else:
            logger.info(f"Znaleziono {len(available_rooms)} dostępnych pokoi.")
        return available_rooms

    def find_rooms_by_type(self, room_type):
        filtered_rooms = [room for room in self.rooms if room.room_type.lower() == room_type.lower()]
        if not filtered_rooms:
            print(f"Brak pokoi typu '{room_type}'.")
            logger.info(f"Brak pokoi typu {room_type} do znalezienia.")
        else:
            logger.info(f"Znaleziono {len(filtered_rooms)} pokoi typu {room_type}.")
        return filtered_rooms

    def find_rooms_by_price_range(self, min_price, max_price):
        filtered_rooms = [room for room in self.rooms if min_price <= room.price <= max_price]
        if not filtered_rooms:
            print(f"Brak pokoi w zakresie cenowym {min_price:.2f}-{max_price:.2f} PLN.")
            logger.info(f"Brak pokoi w zakresie cenowym {min_price}-{max_price} do znalezienia.")
        else:
            logger.info(f"Znaleziono {len(filtered_rooms)} pokoi w zakresie cenowym {min_price}-{max_price}.")
        return filtered_rooms

    def find_rooms_by_amenity(self, amenity):
        filtered_rooms = [room for room in self.rooms if amenity.lower() in [a.lower() for a in room.amenities]]
        if not filtered_rooms:
            print(f"Brak pokoi z udogodnieniem '{amenity}'.")
            logger.info(f"Brak pokoi z udogodnieniem {amenity} do znalezienia.")
        else:
            logger.info(f"Znaleziono {len(filtered_rooms)} pokoi z udogodnieniem {amenity}.")
        return filtered_rooms

    def search_rooms(self, room_type=None, min_price=None, max_price=None, amenity=None, status=None):
        results = self.rooms

        if room_type:
            results = [room for room in results if room.room_type.lower() == room_type.lower()]
        if min_price is not None:
            results = [room for room in results if room.price >= min_price]
        if max_price is not None:
            results = [room for room in results if room.price <= max_price]
        if amenity:
            results = [room for room in results if amenity.lower() in [a.lower() for a in room.amenities]]
        if status:
            results = [room for room in results if room.status.lower() == status.lower()]
        
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
                sorted_list = sorted(rooms_list, key=lambda room: getattr(room, sort_by).lower(), reverse=reverse)
            else: 
                sorted_list = sorted(rooms_list, key=lambda room: getattr(room, sort_by), reverse=reverse)
            logger.info(f"Posortowano pokoje według {sort_by} (odwrócone: {reverse}).")
            return sorted_list
        except AttributeError as e:
            print(f"Błąd: Nie można posortować pokoi według atrybutu '{sort_by}'.")
            logger.error(f"Błąd atrybutu podczas sortowania pokoi ({sort_by}): {e}")
            return rooms_list


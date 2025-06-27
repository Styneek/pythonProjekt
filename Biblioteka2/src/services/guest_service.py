import re
import logging
from src.database.db_manager import DatabaseManager
from src.database.models import Guest

logger = logging.getLogger('hotel_reservation_app')

class GuestService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        logger.info("GuestService zainicjowany (DB).")

    @staticmethod
    def _validate_email(email):
        regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(regex, email)

    def add_guest(self, guest_id, first_name, last_name, id_document, contact_info, is_vip=False, is_loyal_customer=False, preferences=None):
        if self.db_manager.get_guest(guest_id):
            print(f"Błąd: Gość o ID {guest_id} już istnieje.")
            logger.warning(f"Próba dodania istniejącego gościa: {guest_id}")
            return None
        #jezeli podano wgl email sprawdza czy okej
        if "email" in contact_info and not self._validate_email(contact_info["email"]):
            print(f"Błąd: Nieprawidłowy format adresu e-mail: {contact_info['email']}")
            logger.warning(f"Nieprawidłowy format e-maila podczas dodawania gościa: {contact_info['email']}")
            return None

        guest_data = {
            "guest_id": guest_id,
            "first_name": first_name,
            "last_name": last_name,
            "id_document": id_document,
            "contact_info": contact_info,
            "is_vip": is_vip,
            "is_loyal_customer": is_loyal_customer,
            "preferences": preferences or [],
            "loyalty_tier": "Bronze",
            "stay_history": []
        }
        guest = self.db_manager.add_guest(guest_data)
        print(f"Gość {first_name} {last_name} ({guest_id}) został dodany pomyślnie.")
        logger.info(f"Dodano gościa: {guest_id} - {first_name} {last_name}")
        return guest

    def get_guest(self, guest_id):
        guest = self.db_manager.get_guest(guest_id)
        if guest:
            logger.debug(f"Pobrano gościa: {guest_id}")
        else:
            logger.debug(f"Nie znaleziono gościa: {guest_id}")
        return guest

    def update_guest(self, guest_id, **kwargs):#kwargs dowolna liczba arg do aktualizacji
        if "contact_info" in kwargs and "email" in kwargs["contact_info"]:
            if not self._validate_email(kwargs["contact_info"]["email"]):
                print(f"Błąd: Nieprawidłowy format adresu e-mail: {kwargs['contact_info']['email']}")
                logger.warning(f"Nieprawidłowy format e-maila podczas aktualizacji gościa: {kwargs['contact_info']['email']}")
                return None
        guest = self.db_manager.update_guest(guest_id, kwargs)#przekazuje slownik nowych danych
        if guest:
            print(f"Gość {guest_id} został zaktualizowany pomyślnie.")
            logger.info(f"Zaktualizowano gościa: {guest_id} z danymi: {kwargs}")
        else:
            print(f"Błąd: Gość {guest_id} nie znaleziono.")
            logger.warning(f"Próba aktualizacji nieistniejącego gościa: {guest_id}")
        return guest

    def delete_guest(self, guest_id):
        guest = self.db_manager.get_guest(guest_id)
        if guest:
            self.db_manager.db.delete(guest)
            self.db_manager.db.commit()
            print(f"Gość {guest_id} został usunięty pomyślnie.")
            logger.info(f"Usunięto gościa: {guest_id}")
            return True
        print(f"Błąd: Gość {guest_id} nie znaleziono.")
        logger.warning(f"Próba usunięcia nieistniejącego gościa: {guest_id}")
        return False

    def list_all_guests(self):
        guests = self.db_manager.get_all_guests()
        logger.info(f"Pobrano {len(guests)} gości z bazy.")
        if not guests:
            print("Brak gości w systemie.")
            logger.info("Brak gości w systemie do wyświetlenia.")
            return []
        logger.info("Wyświetlono wszystkich gości.")
        return guests

    def add_stay_record_to_guest(self, guest_id, stay_details):
        guest = self.get_guest(guest_id)
        if guest:
            if not guest.stay_history:
                guest.stay_history = []#jak histroia nie istnieje to inicjalizujemy tablice
            guest.stay_history.append(stay_details)
            self.update_guest_loyalty_tier(guest_id)
            self.db_manager.db.commit()
            print(f"Zapis pobytu dodany dla gościa {guest_id}.")
            logger.info(f"Dodano zapis pobytu dla gościa: {guest_id}")
            return True
        print(f"Błąd: Gość {guest_id} nie znaleziono.")
        logger.warning(f"Próba dodania zapisu pobytu dla nieistniejącego gościa: {guest_id}")
        return False

    def update_guest_loyalty_tier(self, guest_id, new_tier=None):
        guest = self.get_guest(guest_id)
        if not guest:
            logger.warning(f"Nie można zaktualizować poziomu lojalności. Gość {guest_id} nie znaleziono.")
            return False
        if new_tier:
            old_tier = guest.loyalty_tier
            guest.loyalty_tier = new_tier
            if old_tier != guest.loyalty_tier:
                print(f"Poziom lojalności gościa {guest_id} zaktualizowany z {old_tier} na {guest.loyalty_tier}.")
                logger.info(f"Poziom lojalności gościa {guest_id} zaktualizowany z {old_tier} na {guest.loyalty_tier}.")
                self.db_manager.db.commit()
            return True
        else:
            num_stays = len(guest.stay_history) if guest.stay_history else 0
            old_tier = guest.loyalty_tier
            if num_stays == 0:
                guest.loyalty_tier = "Bronze"
            elif 1 <= num_stays <= 3:
                guest.loyalty_tier = "Silver"
            elif 4 <= num_stays <= 7:
                guest.loyalty_tier = "Gold"
            else:
                guest.loyalty_tier = "Platinum"
            if old_tier != guest.loyalty_tier:
                print(f"Poziom lojalności gościa {guest_id} zaktualizowany z {old_tier} na {guest.loyalty_tier}.")
                logger.info(f"Poziom lojalności gościa {guest_id} zaktualizowany z {old_tier} na {guest.loyalty_tier}.")
                self.db_manager.db.commit()
            return True

    def search_guests(self, guest_id=None, first_name=None, last_name=None, is_vip=None, is_loyal_customer=None, loyalty_tier=None, contact_info=None):
        guests = self.db_manager.get_all_guests()
        results = guests
        if guest_id:
            results = [guest for guest in results if guest.guest_id.lower() == guest_id.lower()]
        if first_name:
            results = [guest for guest in results if guest.first_name.lower() == first_name.lower()]
        if last_name:
            results = [guest for guest in results if guest.last_name.lower() == last_name.lower()]
        if is_vip is not None:
            results = [guest for guest in results if guest.is_vip == is_vip]
        if is_loyal_customer is not None:
            results = [guest for guest in results if guest.is_loyal_customer == is_loyal_customer]
        if loyalty_tier:
            results = [guest for guest in results if guest.loyalty_tier.lower() == loyalty_tier.lower()]
        if contact_info:
            results = [guest for guest in results if 
                       (guest.contact_info.get('email') and contact_info.lower() in guest.contact_info['email'].lower()) or 
                       (guest.contact_info.get('phone') and contact_info.lower() in guest.contact_info['phone'].lower())
                      ]
        if not results:
            print("Brak gości spełniających podane kryteria.")
            logger.info(f"Brak gości spełniających kryteria wyszukiwania (ID: {guest_id}, Imię: {first_name}, Nazwisko: {last_name}, VIP: {is_vip}, Lojalny: {is_loyal_customer}, Poziom: {loyalty_tier}, Kontakt: {contact_info}).")
        else:
            logger.info(f"Znaleziono {len(results)} gości spełniających kryteria wyszukiwania (ID: {guest_id}, Imię: {first_name}, Nazwisko: {last_name}, VIP: {is_vip}, Lojalny: {is_loyal_customer}, Poziom: {loyalty_tier}, Kontakt: {contact_info}).")
        return results

    def sort_guests(self, guests_list, sort_by, reverse=False):
        if not guests_list:
            print("Brak gości do posortowania.")
            logger.info("Brak gości do posortowania.")
            return []
        valid_keys = ["guest_id", "first_name", "last_name", "is_vip", "is_loyal_customer", "loyalty_tier"]
        if sort_by not in valid_keys:
            print(f"Błąd: Nieprawidłowe kryterium sortowania dla gości: {sort_by}. Dostępne: {', '.join(valid_keys)}.")
            logger.warning(f"Nieprawidłowe kryterium sortowania gości: {sort_by}")
            return guests_list
        try:
            if sort_by in ["guest_id", "first_name", "last_name", "loyalty_tier"]:
                if sort_by == "loyalty_tier":
                    tier_order = {"Bronze": 0, "Silver": 1, "Gold": 2, "Platinum": 3}
                    sorted_list = sorted(guests_list, key=lambda guest: tier_order.get(guest.loyalty_tier, 99), reverse=reverse)
                else:
                    sorted_list = sorted(guests_list, key=lambda guest: getattr(guest, sort_by).lower(), reverse=reverse)
            else:
                sorted_list = sorted(guests_list, key=lambda guest: getattr(guest, sort_by), reverse=reverse)
            logger.info(f"Posortowano gości według {sort_by} (odwrócone: {reverse}).")
            return sorted_list
        except AttributeError as e:
            print(f"Błąd: Nie można posortować gości według atrybutu '{sort_by}'.")
            logger.error(f"Błąd atrybutu podczas sortowania gości ({sort_by}): {e}")
            return guests_list
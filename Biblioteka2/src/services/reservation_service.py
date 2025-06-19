import logging
from src.models.reservation import Reservation
from src.data.data_manager import DataManager
from src.services.room_service import RoomService
from src.services.guest_service import GuestService
from datetime import datetime, timedelta
from src.services.housekeeping_service import HousekeepingService
from src.services.discount_service import DiscountService
from src.models.room import Room
from src.models.guest import Guest

logger = logging.getLogger('hotel_reservation_app') 

class ReservationService:
    def __init__(self, data_manager: DataManager, room_service: RoomService, guest_service: GuestService, housekeeping_service: HousekeepingService, discount_service: DiscountService):
        self.data_manager = data_manager
        self.room_service = room_service
        self.guest_service = guest_service
        self.housekeeping_service = housekeeping_service
        self.discount_service = discount_service
        self.reservations = self.data_manager.load_reservations()
        logger.info("ReservationService zainicjowany.")

    def _save_reservations(self):
        self.data_manager.save_reservations(self.reservations)
        logger.debug("Zapisano rezerwacje do pliku.")

    def create_reservation(self, guest_id, room_number, check_in_date_str, check_out_date_str, discount_code=None):
        guest = self.guest_service.get_guest(guest_id)
        room = self.room_service.get_room(room_number)

        if not guest:
            print(f"Błąd: Nie znaleziono gościa o ID {guest_id}.")
            logger.warning(f"Próba utworzenia rezerwacji dla nieistniejącego gościa: {guest_id}")
            return None
        if not room:
            print(f"Błąd: Nie znaleziono pokoju o numerze {room_number}.")
            logger.warning(f"Próba utworzenia rezerwacji dla nieistniejącego pokoju: {room_number}")
            return None

        try:
            check_in_date = datetime.strptime(check_in_date_str, "%Y-%m-%d")
            check_out_date = datetime.strptime(check_out_date_str, "%Y-%m-%d")
        except ValueError as e:
            print("Błąd: Nieprawidłowy format daty. Proszę użyć formatu RRRR-MM-DD (np. 2024-05-01).")
            logger.error(f"Błąd formatu daty podczas tworzenia rezerwacji: {check_in_date_str}, {check_out_date_str} - {e}")
            return None

        if check_in_date >= check_out_date:
            print("Błąd: Data wymeldowania musi być późniejsza niż data zameldowania.")
            logger.warning(f"Nieprawidłowe daty rezerwacji (data wymeldowania przed datą zameldowania): {check_in_date_str} - {check_out_date_str}")
            return None

        if not self.is_room_available(room_number, check_in_date_str, check_out_date_str):
            print(f"Błąd: Pokój {room_number} nie jest dostępny w wybranym terminie ({check_in_date_str} do {check_out_date_str}).")
            logger.info(f"Pokój {room_number} niedostępny w wybranym terminie ({check_in_date_str} do {check_out_date_str}).")
            return None

        
        reservation_id = f"RES{len(self.reservations) + 1:04d}"
        stay_duration_days = (check_out_date - check_in_date).days
        original_price = room.price * stay_duration_days
        total_price = original_price
        applied_discount = None

        guest_loyalty_tier = guest.loyalty_tier if guest else None  

        if discount_code:
            discount = self.discount_service.get_discount(discount_code)
            if discount and discount.is_valid(datetime.now().strftime("%Y-%m-%d"), room.room_type, guest.guest_id, stay_duration_days, guest_loyalty_tier):
                discount_amount = discount.calculate_discount_amount(original_price)
                total_price = original_price - discount_amount
                applied_discount = discount.discount_id
                print(f"Zastosowano rabat '{discount.code}'. Zniżka: {discount_amount:.2f} PLN.")
                logger.info(f"Zastosowano rabat {discount.code} dla rezerwacji {reservation_id}. Zniżka: {discount_amount:.2f} PLN.")
            else:
                print(f"Ostrzeżenie: Podany kod rabatowy '{discount_code}' jest nieprawidłowy lub nie ma zastosowania.")
                logger.warning(f"Podany kod rabatowy {discount_code} jest nieprawidłowy lub nie ma zastosowania dla rezerwacji {reservation_id}.")
        else: 
            applicable_loyalty_discounts = self.discount_service.find_applicable_discounts(
                check_date_str=datetime.now().strftime("%Y-%m-%d"),
                room_type=room.room_type,
                guest_id=guest.guest_id,
                stay_duration_days=stay_duration_days,
                guest_loyalty_tier=guest_loyalty_tier
            )
            auto_applicable_discounts = [d for d in applicable_loyalty_discounts if d.applicable_loyalty_tiers]

            if auto_applicable_discounts:
                best_discount = None
                max_discount_amount = 0

                for d in auto_applicable_discounts:
                    current_discount_amount = d.calculate_discount_amount(original_price)
                    if current_discount_amount > max_discount_amount:
                        max_discount_amount = current_discount_amount
                        best_discount = d

                if best_discount:
                    total_price = original_price - max_discount_amount
                    applied_discount = best_discount.discount_id
                    print(f"Automatycznie zastosowano rabat lojalnościowy '{best_discount.code}'. Zniżka: {max_discount_amount:.2f} PLN.")
                    logger.info(f"Automatycznie zastosowano rabat lojalnościowy {best_discount.code} dla rezerwacji {reservation_id}. Zniżka: {max_discount_amount:.2f} PLN.")

        reservation = Reservation(reservation_id, guest_id, room_number, check_in_date_str, check_out_date_str, total_price=total_price)
        if applied_discount: 
            reservation.applied_discount_id = applied_discount
            

        self.reservations.append(reservation)
        self._save_reservations()
        self.room_service.update_room_status(room_number, "zajęty") 
        self.guest_service.add_stay_record_to_guest(guest_id, {"reservation_id": reservation_id, "room_number": room_number, "check_in": check_in_date_str, "check_out": check_out_date_str})

        print(f"Rezerwacja {reservation_id} została utworzona pomyślnie dla Pokoju {room_number} przez Gościa {guest_id}. Całkowita cena: {total_price:.2f}.")
        logger.info(f"Utworzono rezerwację {reservation_id} dla pokoju {room_number} i gościa {guest_id}. Całkowita cena: {total_price:.2f}.")
        return reservation

    def get_reservation(self, reservation_id):
        reservation = next((res for res in self.reservations if res.reservation_id == reservation_id), None)
        if reservation:
            logger.debug(f"Pobrano rezerwację: {reservation_id}")
        else:
            logger.debug(f"Nie znaleziono rezerwacji: {reservation_id}")
        return reservation

    def update_reservation(self, reservation_id, **kwargs):
        reservation = self.get_reservation(reservation_id)
        if reservation:
            for key, value in kwargs.items():
                setattr(reservation, key, value)
            self._save_reservations()
            print(f"Rezerwacja {reservation_id} została zaktualizowana pomyślnie.")
            logger.info(f"Zaktualizowano rezerwację: {reservation_id} z danymi: {kwargs}")
            return reservation
        print(f"Błąd: Rezerwacja {reservation_id} nie znaleziono.")
        logger.warning(f"Próba aktualizacji nieistniejącej rezerwacji: {reservation_id}")
        return None

    def cancel_reservation(self, reservation_id, charge_cancellation_fee=False):
        reservation = self.get_reservation(reservation_id)
        if reservation:
            if reservation.status == "cancelled":
                print(f"Rezerwacja {reservation_id} jest już anulowana.")
                logger.info(f"Rezerwacja {reservation_id} jest już anulowana.")
                return False

            reservation.update_status("cancelled")
            self._save_reservations()
            self.room_service.update_room_status(reservation.room_number, "dostępny") 

            if charge_cancellation_fee:
                print(f"Opłata za anulowanie naliczona dla rezerwacji {reservation_id}.")
                logger.info(f"Opłata za anulowanie naliczona dla rezerwacji {reservation_id}.")

            print(f"Rezerwacja {reservation_id} została anulowana pomyślnie.")
            logger.info(f"Anulowano rezerwację: {reservation_id}")
            return True
        print(f"Błąd: Rezerwacja {reservation_id} nie znaleziono.")
        logger.warning(f"Próba anulowania nieistniejącej rezerwacji: {reservation_id}")
        return False

    def check_in_guest(self, reservation_id):
        reservation = self.get_reservation(reservation_id)
        if not reservation:
            print(f"Błąd: Rezerwacja {reservation_id} nie znaleziono.")
            logger.warning(f"Próba zameldowania dla nieistniejącej rezerwacji: {reservation_id}")
            return False
        if reservation.status != "active":
            print(f"Błąd: Rezerwacja {reservation_id} nie jest w statusie aktywnego i nie może być zameldowana.")
            logger.warning(f"Próba zameldowania nieaktywnej rezerwacji {reservation_id} (status: {reservation.status}).")
            return False

        room = self.room_service.get_room(reservation.room_number)
        if not room:
            print(f"Błąd: Pokój {reservation.room_number} nie znaleziono dla rezerwacji {reservation_id}.")
            logger.error(f"Pokój {reservation.room_number} nie znaleziono dla rezerwacji {reservation_id} podczas zameldowania.")
            return False
        
        if room.status not in ["zajęty", "dostępny"]:
            print(f"Błąd: Pokój {room.number} nie jest w odpowiednim statusie do zameldowania (obecny status: {room.status}).")
            logger.warning(f"Pokój {room.number} nie jest w odpowiednim statusie do zameldowania (status: {room.status}) dla rezerwacji {reservation_id}.")
            return False

        reservation.update_status("checked_in")
        self._save_reservations()

        if room.status == "dostępny":
            self.room_service.update_room_status(room.number, "zajęty")
            logger.info(f"Zaktualizowano status pokoju {room.number} na 'zajęty' podczas zameldowania rezerwacji {reservation_id}.")

        logger.info(f"Zameldowano gościa dla Rezerwacji {reservation_id} do Pokoju {room.number}.")
        print(f"Gość zameldowany dla Rezerwacji {reservation_id} do Pokoju {room.number}.")
        return True

    def check_out_guest(self, reservation_id, room_cleaning_needed=False, late_checkout_fee=0.0):
        reservation = self.get_reservation(reservation_id)
        if not reservation:
            print(f"Błąd: Rezerwacja {reservation_id} nie znaleziono.")
            logger.warning(f"Próba wymeldowania dla nieistniejącej rezerwacji: {reservation_id}")
            return False
        if reservation.status != "checked_in" and reservation.status != "active":
            print(f"Błąd: Rezerwacja {reservation_id} nie jest aktywna lub zameldowana i nie może być wymeldowana.")
            logger.warning(f"Próba wymeldowania nieaktywnej/niezameldowanej rezerwacji {reservation_id} (status: {reservation.status}).")
            return False

        room = self.room_service.get_room(reservation.room_number)
        if not room:
            print(f"Błąd: Pokój {reservation.room_number} nie znaleziono dla rezerwacji {reservation_id}.")
            logger.error(f"Pokój {reservation.room_number} nie znaleziono dla rezerwacji {reservation_id} podczas wymeldowania.")
            return False
 
        current_date = datetime.now().date()
        reservation_checkout_date = datetime.strptime(reservation.check_out_date, "%Y-%m-%d").date()

        if current_date > reservation_checkout_date and late_checkout_fee <= 0:
             print(f"Ostrzeżenie: Gość wymeldowuje się po terminie ({reservation_checkout_date}). Rozważ naliczenie dodatkowej opłaty.")
             logger.warning(f"Gość wymeldowuje się po terminie ({reservation_checkout_date}) dla rezerwacji {reservation_id}.")
        elif current_date > reservation_checkout_date and late_checkout_fee > 0:
            print(f"Naliczono opłatę za późne wymeldowanie: {late_checkout_fee:.2f} PLN.")
            logger.info(f"Naliczono opłatę za późne wymeldowanie {late_checkout_fee:.2f} PLN dla rezerwacji {reservation_id}.")
            reservation.total_price += late_checkout_fee
            print(f"Dodano opłatę za późne wymeldowanie w wysokości {late_checkout_fee:.2f} do rezerwacji {reservation_id}.")
 
        reservation.update_status("checked_out")
        self._save_reservations()

        if room_cleaning_needed:
            self.room_service.update_room_status(room.number, "sprzątanie")
            self.housekeeping_service.create_task(room.number, "Nieprzypisane", reservation.check_out_date, f"Sprzątanie po wymeldowaniu rezerwacji {reservation_id}")
            logger.info(f"Utworzono zadanie sprzątania dla pokoju {room.number} po wymeldowaniu rezerwacji {reservation_id}.")
            self.room_service.update_room_status(room.number, "dostępny")
        else:
            self.room_service.update_room_status(room.number, "dostępny")
            logger.info(f"Status pokoju {room.number} zmieniono na 'dostępny' (bez sprzątania) po wymeldowaniu rezerwacji {reservation_id}.")

        print(f"Gość wymeldowany z Rezerwacji {reservation_id} z Pokoju {room.number}.")
        logger.info(f"Wymeldowano gościa dla Rezerwacji {reservation_id} z Pokoju {room.number}.")
        return True

    def is_room_available(self, room_number, check_in_date_str, check_out_date_str):
        room = self.room_service.get_room(room_number)
        if not room:
            logger.warning(f"Sprawdzanie dostępności: Pokój {room_number} nie znaleziono.")
            return False
        if room.status != "dostępny":
            logger.info(f"Sprawdzanie dostępności: Pokój {room_number} nie jest dostępny (status: {room.status}).")
            return False

        try:
            check_in_date = datetime.strptime(check_in_date_str, "%Y-%m-%d")
            check_out_date = datetime.strptime(check_out_date_str, "%Y-%m-%d")
        except ValueError as e:
            logger.error(f"Błąd formatu daty podczas sprawdzania dostępności pokoju: {check_in_date_str}, {check_out_date_str} - {e}")
            return False 

        for res in self.reservations:
            if res.room_number == room_number and res.status == "active":
                res_check_in = datetime.strptime(res.check_in_date, "%Y-%m-%d")
                res_check_out = datetime.strptime(res.check_out_date, "%Y-%m-%d")
 
                if not (check_out_date <= res_check_in or check_in_date >= res_check_out):
                    logger.info(f"Pokój {room_number} jest zajęty przez rezerwację {res.reservation_id} w terminie {check_in_date_str} do {check_out_date_str}.")
                    return False
        logger.info(f"Pokój {room_number} jest dostępny w terminie {check_in_date_str} do {check_out_date_str}.")
        return True

    def list_all_reservations(self):
        if not self.reservations:
            print("Brak rezerwacji w systemie.")
            logger.info("Brak rezerwacji w systemie do wyświetlenia.")
            return []
        logger.info("Wyświetlono wszystkie rezerwacje.")
        return self.reservations

    def search_reservations(self, reservation_id=None, guest_id=None, room_number=None, status=None, payment_status=None, check_in_date_range=None):
        results = self.reservations

        if reservation_id:
            results = [res for res in results if res.reservation_id.lower() == reservation_id.lower()]
        if guest_id:
            results = [res for res in results if res.guest_id.lower() == guest_id.lower()]
        if room_number:
            results = [res for res in results if res.room_number.lower() == room_number.lower()]
        if status:
            results = [res for res in results if res.status.lower() == status.lower()]
        if payment_status:
            results = [res for res in results if hasattr(res, 'payment_status') and res.payment_status.lower() == payment_status.lower()]

        if check_in_date_range and (check_in_date_range[0] or check_in_date_range[1]):
            start_date_str, end_date_str = check_in_date_range
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None

                if start_date and end_date and start_date > end_date:
                    logger.warning(f"Błąd: Data początkowa ({start_date_str}) jest po dacie końcowej ({end_date_str}) w wyszukiwaniu rezerwacji.")
                    return []

                filtered_by_date = []
                for res in results:
                    res_check_in = datetime.strptime(res.check_in_date, "%Y-%m-%d").date()
                    if (start_date is None or res_check_in >= start_date) and \
                       (end_date is None or res_check_in <= end_date):
                        filtered_by_date.append(res)
                results = filtered_by_date
            except ValueError as e:
                print(f"Błąd: Nieprawidłowy format daty w zakresie wyszukiwania. Użyj YYYY-MM-DD. Szczegóły: {e}")
                logger.error(f"Błąd formatu daty w wyszukiwaniu rezerwacji: {check_in_date_range} - {e}")
                return []

        if not results:
            print("Brak rezerwacji spełniających podane kryteria.")
            logger.info(f"Brak rezerwacji spełniających kryteria wyszukiwania (ID: {reservation_id}, Gość: {guest_id}, Pokój: {room_number}, Status: {status}, Status płatności: {payment_status}, Zakres dat: {check_in_date_range}).")
        else:
            logger.info(f"Znaleziono {len(results)} rezerwacji spełniających kryteria wyszukiwania (ID: {reservation_id}, Gość: {guest_id}, Pokój: {room_number}, Status: {status}, Status płatności: {payment_status}, Zakres dat: {check_in_date_range}).")
        return results

    def sort_reservations(self, reservations_list, sort_by, reverse=False):
        if not reservations_list:
            print("Brak rezerwacji do posortowania.")
            logger.info("Brak rezerwacji do posortowania.")
            return []
        
        valid_keys = ["reservation_id", "guest_id", "room_number", "check_in_date", "check_out_date", "status", "total_price", "payment_status"]

        if sort_by not in valid_keys:
            print(f"Błąd: Nieprawidłowe kryterium sortowania dla rezerwacji: {sort_by}. Dostępne: {', '.join(valid_keys)}.")
            logger.warning(f"Nieprawidłowe kryterium sortowania rezerwacji: {sort_by}")
            return reservations_list
        
        try:
            if sort_by in ["check_in_date", "check_out_date"]:
                sorted_list = sorted(reservations_list, key=lambda res: datetime.strptime(getattr(res, sort_by), "%Y-%m-%d"), reverse=reverse)
            elif sort_by == "total_price":
                sorted_list = sorted(reservations_list, key=lambda res: float(getattr(res, sort_by)), reverse=reverse)
            else:
                sorted_list = sorted(reservations_list, key=lambda res: str(getattr(res, sort_by)).lower(), reverse=reverse)
            logger.info(f"Posortowano rezerwacje według {sort_by} (odwrócone: {reverse}).")
            return sorted_list
        except AttributeError as e:
            print(f"Błąd: Nie można posortować rezerwacji według atrybutu '{sort_by}'.")
            logger.error(f"Błąd atrybutu podczas sortowania rezerwacji ({sort_by}): {e}")
            return reservations_list

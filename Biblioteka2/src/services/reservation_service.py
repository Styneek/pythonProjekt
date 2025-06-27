import logging
from src.database.db_manager import DatabaseManager
from src.database.models import Reservation
from src.services.room_service import RoomService
from src.services.guest_service import GuestService
from datetime import datetime, timedelta
from src.services.housekeeping_service import HousekeepingService
from src.services.discount_service import DiscountService

logger = logging.getLogger('hotel_reservation_app')

class ReservationService:
    def __init__(self, db_manager: DatabaseManager, room_service: RoomService, guest_service: GuestService, housekeeping_service: HousekeepingService, discount_service: DiscountService):
        self.db_manager = db_manager #tworzy polaczenie z baza
        #dostep do logiki pokoi/gosci/sprzatania/rabatow
        self.room_service = room_service
        self.guest_service = guest_service
        self.housekeeping_service = housekeeping_service
        self.discount_service = discount_service
        logger.info("ReservationService zainicjowany (DB).")

#sprawdza czy dany rabat jest wazny dla rezerwacji konkretnej
    def _is_discount_valid(self, discount, check_date_str=None, room_type=None, guest_id=None, stay_duration_days=0, guest_loyalty_tier=None):
        if not discount.is_active:
            return False
        current_date = datetime.now().date()
        if check_date_str:
            try:
                check_date = datetime.strptime(check_date_str, "%Y-%m-%d").date()
            except ValueError:
                return False
        else:
            check_date = current_date
            #sprawdzam dzy data miesci sie w widelkach podanych
        if discount.valid_from and check_date < discount.valid_from.date():
            return False
        if discount.valid_to and check_date > discount.valid_to.date():
            return False
        #jak jest np min 3 dni a ktos 2 to odrzuca rabat
        if discount.min_stay_days > 0 and stay_duration_days < discount.min_stay_days:
            return False
        #pobieram liste okreslonego rabatu, jesli none to [] zeby bledow nie bylo
        room_types = discount.applicable_room_types if discount.applicable_room_types is not None else []
        guest_ids = discount.applicable_guest_ids if discount.applicable_guest_ids is not None else []
        loyalty_tiers = discount.applicable_loyalty_tiers if discount.applicable_loyalty_tiers is not None else []
        #sprawdzam czy rabat dotyczy pokoju/goscia/lojalnosci
        if room_types and room_type not in room_types:
            return False
        if guest_ids and guest_id not in guest_ids:
            return False
        if loyalty_tiers and guest_loyalty_tier not in loyalty_tiers:
            return False
        return True#jezeli wazny dla danej rezerwacji

#obiekt rabatu albo procentowy/stala cena
    def _calculate_discount_amount(self, discount, original_price):
        if discount.percentage > 0:
            return original_price * (discount.percentage / 100)
        elif discount.fixed_amount > 0:
            return discount.fixed_amount
        return 0

    def create_reservation(self, guest_id, room_number, check_in_date_str, check_out_date_str, discount_code=None):
        #pobieram goscia/pokoj z bazy
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
            #stringi na obiekty datetime
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
#sprawdzam czy pokoj jest dostepny
        if not self.is_room_available(room_number, check_in_date_str, check_out_date_str):
            print(f"Błąd: Pokój {room_number} nie jest dostępny w wybranym terminie ({check_in_date_str} do {check_out_date_str}).")
            logger.info(f"Pokój {room_number} niedostępny w wybranym terminie ({check_in_date_str} do {check_out_date_str}).")
            return None

        reservation_id = f"RES{len(self.db_manager.get_all_reservations()) + 1:04d}"
        #obliczam ile trwa pobyt i cene
        stay_duration_days = (check_out_date - check_in_date).days
        original_price = room.price * stay_duration_days
        total_price = original_price
        applied_discount = None

        guest_loyalty_tier = getattr(guest, 'loyalty_tier', None)
#jezeli rabat
        if discount_code:
            discount = self.discount_service.get_discount(discount_code) #pobieram rabat
            #sprawdzam czy jest wazny
            if discount and self._is_discount_valid(discount, datetime.now().strftime("%Y-%m-%d"), room.room_type, guest.guest_id, stay_duration_days, guest_loyalty_tier):
                discount_amount = self._calculate_discount_amount(discount, original_price)
                total_price = original_price - discount_amount
                applied_discount = discount.discount_id
                print(f"Zastosowano rabat '{discount.code}'. Zniżka: {discount_amount:.2f} PLN.")
                logger.info(f"Zastosowano rabat {discount.code} dla rezerwacji {reservation_id}. Zniżka: {discount_amount:.2f} PLN.")
            else:
                print(f"Ostrzeżenie: Podany kod rabatowy '{discount_code}' jest nieprawidłowy lub nie ma zastosowania.")
                logger.warning(f"Podany kod rabatowy {discount_code} jest nieprawidłowy lub nie ma zastosowania dla rezerwacji {reservation_id}.")
        #automatycznie szukam dostepnych rabatow ktore pasuja do...         
        else:
            applicable_loyalty_discounts = self.discount_service.find_applicable_discounts(
                check_date_str=datetime.now().strftime("%Y-%m-%d"),
                room_type=room.room_type,
                guest_id=guest.guest_id,
                stay_duration_days=stay_duration_days,
                guest_loyalty_tier=guest_loyalty_tier
            )
            #tylko rabaty lojalnosciowe/ getattr probuje pobrac atrybut applicable_loyalty_discounts
            auto_applicable_discounts = [d for d in applicable_loyalty_discounts if getattr(d, 'applicable_loyalty_tiers', None)]

            if auto_applicable_discounts:
                best_discount = None
                max_discount_amount = 0
                #dla kazdego rabatu oblicza wartosc
                for d in auto_applicable_discounts:#przegladam kazdy rabat
                    current_discount_amount = self._calculate_discount_amount(d, original_price)#obliczam
                    #zapamietuje najlepszy rabat jak jest lepszy to nadpisuje
                    if current_discount_amount > max_discount_amount:
                        max_discount_amount = current_discount_amount
                        best_discount = d
                #jesli znaleziono
                if best_discount:
                    total_price = original_price - max_discount_amount #odejmuje rabat
                    applied_discount = best_discount.discount_id#zapisuje id
                    print(f"Automatycznie zastosowano rabat lojalnościowy '{best_discount.code}'. Zniżka: {max_discount_amount:.2f} PLN.")
                    logger.info(f"Automatycznie zastosowano rabat lojalnościowy {best_discount.code} dla rezerwacji {reservation_id}. Zniżka: {max_discount_amount:.2f} PLN.")
        #slownik rezerwacji
        reservation_data = {
            'reservation_id': reservation_id,
            'guest_id': guest_id,
            'room_number': room_number,
            'check_in': check_in_date,
            'check_out': check_out_date,
            'total_price': total_price,
            'status': 'active'
        }
        reservation = self.db_manager.add_reservation(reservation_data)#zwraca utworzony obiekt
        if applied_discount:
            #dodaje rabat lokalnie a potem do bazy
            reservation.applied_discount_id = applied_discount
            self.db_manager.update_reservation(reservation_id, {'applied_discount_id': applied_discount})

        self.room_service.update_room_status(room_number, "zajęty")
        #dodaje do history klienta informacje o pobycie
        self.guest_service.add_stay_record_to_guest(guest_id, {"reservation_id": reservation_id, "room_number": room_number, "check_in": check_in_date_str, "check_out": check_out_date_str})

        print(f"Rezerwacja {reservation_id} została utworzona pomyślnie dla Pokoju {room_number} przez Gościa {guest_id}. Całkowita cena: {total_price:.2f}.")
        logger.info(f"Utworzono rezerwację {reservation_id} dla pokoju {room_number} i gościa {guest_id}. Całkowita cena: {total_price:.2f}.")
        return reservation

    def get_reservation(self, reservation_id):
        reservation = self.db_manager.get_reservation(reservation_id)#pobieram po id z bazy
        if reservation:
            logger.debug(f"Pobrano rezerwację: {reservation_id}")
        else:
            logger.debug(f"Nie znaleziono rezerwacji: {reservation_id}")
        return reservation

    def update_reservation(self, reservation_id, **kwargs):#kwargs dowolna liczbna arg do aktualizacji
        reservation = self.db_manager.update_reservation(reservation_id, kwargs)
        if reservation:
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

            reservation.status = "cancelled"#zmieniam status
            self.db_manager.update_reservation(reservation_id, {'status': 'cancelled'})
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
        reservation = self.get_reservation(reservation_id)#pobieram po id
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

        reservation.status = "checked_in"
        self.db_manager.update_reservation(reservation_id, {'status': 'checked_in'})

        if room.status == "dostępny":
            self.room_service.update_room_status(room.number, "zajęty")
            logger.info(f"Zaktualizowano status pokoju {room.number} na 'zajęty' podczas zameldowania rezerwacji {reservation_id}.")

        logger.info(f"Zameldowano gościa dla Rezerwacji {reservation_id} do Pokoju {room.number}.")
        print(f"Gość zameldowany dla Rezerwacji {reservation_id} do Pokoju {room.number}.")
        return True

    def check_out_guest(self, reservation_id, room_cleaning_needed=False, late_checkout_fee=0.0):
        reservation = self.get_reservation(reservation_id)#pobieram rezerwacje
        if not reservation:
            print(f"Błąd: Rezerwacja {reservation_id} nie znaleziono.")
            logger.warning(f"Próba wymeldowania dla nieistniejącej rezerwacji: {reservation_id}")
            return False
        if reservation.status not in ["checked_in", "active"]:
            print(f"Błąd: Rezerwacja {reservation_id} nie jest aktywna lub zameldowana i nie może być wymeldowana.")
            logger.warning(f"Próba wymeldowania nieaktywnej/niezameldowanej rezerwacji {reservation_id} (status: {reservation.status}).")
            return False

        room = self.room_service.get_room(reservation.room_number)
        if not room:
            print(f"Błąd: Pokój {reservation.room_number} nie znaleziono dla rezerwacji {reservation_id}.")
            logger.error(f"Pokój {reservation.room_number} nie znaleziono dla rezerwacji {reservation_id} podczas wymeldowania.")
            return False

        current_date = datetime.now().date()#pobieram date
        reservation_checkout_date = reservation.check_out.date() if hasattr(reservation.check_out, 'date') else reservation.check_out#pobieram date planowanego wymeldowania/hasattr sprawdza czy jest atrybut

        if current_date > reservation_checkout_date and late_checkout_fee > 0:
            print(f"Naliczono opłatę za późne wymeldowanie: {late_checkout_fee:.2f} PLN.")
            logger.info(f"Naliczono opłatę za późne wymeldowanie {late_checkout_fee:.2f} PLN dla rezerwacji {reservation_id}.")
            reservation.total_price += late_checkout_fee
            self.db_manager.update_reservation(reservation_id, {'total_price': reservation.total_price})
            print(f"Dodano opłatę za późne wymeldowanie w wysokości {late_checkout_fee:.2f} do rezerwacji {reservation_id}.")

        reservation.status = "checked_out"
        self.db_manager.update_reservation(reservation_id, {'status': 'checked_out'})

        if room_cleaning_needed:
            self.room_service.update_room_status(room.number, "sprzątanie")
            self.housekeeping_service.create_task(room.number, "Nieprzypisane", reservation.check_out.strftime("%Y-%m-%d"), f"Sprzątanie po wymeldowaniu rezerwacji {reservation_id}")
            logger.info(f"Utworzono zadanie sprzątania dla pokoju {room.number} po wymeldowaniu rezerwacji {reservation_id}.")
            self.room_service.update_room_status(room.number, "dostępny")
        else:
            self.room_service.update_room_status(room.number, "dostępny")
            logger.info(f"Status pokoju {room.number} zmieniono na 'dostępny' (bez sprzątania) po wymeldowaniu rezerwacji {reservation_id}.")

        print(f"Gość wymeldowany z Rezerwacji {reservation_id} z Pokoju {room.number}.")
        logger.info(f"Wymeldowano gościa dla Rezerwacji {reservation_id} z Pokoju {room.number}.")
        return True

    def is_room_available(self, room_number, check_in_date_str, check_out_date_str):
        room = self.room_service.get_room(room_number)#pobieram pokoj
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

        reservations = self.db_manager.get_all_reservations()
        for res in reservations:
            if res.room_number == room_number and res.status == "active":
                res_check_in = res.check_in if isinstance(res.check_in, datetime) else datetime.strptime(res.check_in, "%Y-%m-%d")
                res_check_out = res.check_out if isinstance(res.check_out, datetime) else datetime.strptime(res.check_out, "%Y-%m-%d")
                if not (check_out_date <= res_check_in or check_in_date >= res_check_out):#jezeli wymeldowanie przed / i zameldowanie po
                    logger.info(f"Pokój {room_number} jest zajęty przez rezerwację {res.reservation_id} w terminie {check_in_date_str} do {check_out_date_str}.")
                    return False
        logger.info(f"Pokój {room_number} jest dostępny w terminie {check_in_date_str} do {check_out_date_str}.")
        return True

    def list_all_reservations(self):
        reservations = self.db_manager.get_all_reservations()
        if not reservations:
            print("Brak rezerwacji w systemie.")
            logger.info("Brak rezerwacji w systemie do wyświetlenia.")
            return []
        logger.info("Wyświetlono wszystkie rezerwacje.")
        return reservations

    def search_reservations(self, reservation_id=None, guest_id=None, room_number=None, status=None, payment_status=None, check_in_date_range=None):
        reservations = self.db_manager.get_all_reservations()
        results = reservations

        if reservation_id:
            results = [res for res in results if res.reservation_id.lower() == reservation_id.lower()]
        if guest_id:
            results = [res for res in results if res.guest_id.lower() == guest_id.lower()]
        if room_number:
            results = [res for res in results if res.room_number.lower() == room_number.lower()]
        if status:
            results = [res for res in results if res.status.lower() == status.lower()]
        if payment_status:
            results = [res for res in results if hasattr(res, 'payment_status') and res.payment_status and res.payment_status.lower() == payment_status.lower()]
        #zakres dat
        if check_in_date_range and (check_in_date_range[0] or check_in_date_range[1]):
            start_date_str, end_date_str = check_in_date_range
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None

                if start_date and end_date and start_date > end_date:
                    logger.warning(f"Błąd: Data początkowa ({start_date_str}) jest po dacie końcowej ({end_date_str}) w wyszukiwaniu rezerwacji.")
                    return []

                filtered_by_date = []#jezeli zakres dat ok to tu je trzymam(rezerwacje)
                for res in results:
                    res_check_in = res.check_in.date() if isinstance(res.check_in, datetime) else datetime.strptime(res.check_in, "%Y-%m-%d").date()
                    if (start_date is None or res_check_in >= start_date) and \
                       (end_date is None or res_check_in <= end_date):
                        filtered_by_date.append(res)#jak spelnia warunek to dodaje
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

        valid_keys = ["reservation_id", "guest_id", "room_number", "check_in", "check_out", "status", "total_price"]

        #sprawdzam czy prawidlowa opcja
        if sort_by not in valid_keys:
            print(f"Błąd: Nieprawidłowe kryterium sortowania dla rezerwacji: {sort_by}. Dostępne: {', '.join(valid_keys)}.")
            logger.warning(f"Nieprawidłowe kryterium sortowania rezerwacji: {sort_by}")
            return reservations_list

        try:
            #sortowanie po dacie
            if sort_by in ["check_in", "check_out"]:
                sorted_list = sorted(reservations_list, key=lambda res: res.check_in if isinstance(res.check_in, datetime) else datetime.strptime(res.check_in, "%Y-%m-%d"), reverse=reverse)
            #po cenie/getattr pobiera wartosc atrybutu z obiektu
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

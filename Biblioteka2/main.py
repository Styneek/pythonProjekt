import argparse
import os
import json
import logging
from datetime import datetime, timedelta
from colorama import Fore, Style, init

from src.data.data_manager import DataManager
from src.services.room_service import RoomService
from src.services.guest_service import GuestService
from src.services.reservation_service import ReservationService
from src.services.report_service import ReportService
from src.services.payment_service import PaymentService
from src.services.housekeeping_service import HousekeepingService
from src.services.user_service import UserService
from src.models.user import User
from src.services.discount_service import DiscountService
from src.utils.logger_config import setup_logging
from src.constants.status_mappings import (
    ROOM_STATUSES, ROOM_STATUS_MAPPING, REVERSE_ROOM_STATUS_MAPPING,
    RESERVATION_STATUSES, RESERVATION_STATUS_MAPPING, REVERSE_RESERVATION_STATUS_MAPPING,
    PAYMENT_STATUSES, PAYMENT_STATUS_MAPPING, REVERSE_PAYMENT_STATUS_MAPPING,
    INVOICE_STATUSES, INVOICE_STATUS_MAPPING, REVERSE_INVOICE_STATUS_MAPPING,
    HOUSEKEEPING_TASK_STATUSES, HOUSEKEEPING_STATUS_MAPPING, REVERSE_HOUSEKEEPING_STATUS_MAPPING
)
from src.database.db_manager import DatabaseManager

ROOM_TYPES = ["pojedynczy", "podwójny", "apartament"]
GUEST_LOYALTY_TIERS = ["Bronze", "Silver", "Gold", "Platinum"]
PAYMENT_METHODS = ["karta", "gotówka", "przelew"]
HOUSEKEEPING_TASK_STATUSES = ["oczekujące", "w trakcie", "ukończone", "anulowane"]
USER_ROLES = ["administrator", "recepcjonista", "pokojówka"]
RESERVATION_STATUSES = ["aktywna", "anulowana", "zameldowana", "wymeldowana"]
PAYMENT_STATUSES = ["oczekująca", "opłacona", "częściowo opłacona"]

REVERSE_ROOM_STATUS_MAPPING = {v: k for k, v in ROOM_STATUS_MAPPING.items()}
REVERSE_RESERVATION_STATUS_MAPPING = {v: k for k, v in RESERVATION_STATUS_MAPPING.items()}
REVERSE_PAYMENT_STATUS_MAPPING = {v: k for k, v in PAYMENT_STATUS_MAPPING.items()}
REVERSE_INVOICE_STATUS_MAPPING = {v: k for k, v in INVOICE_STATUS_MAPPING.items()}
REVERSE_HOUSEKEEPING_STATUS_MAPPING = {v: k for k, v in HOUSEKEEPING_STATUS_MAPPING.items()}

init(autoreset=True)

setup_logging()
logger = logging.getLogger('hotel_reservation_app')

def display_table(data_list, headers_map, title="Wyniki"):
    #jak lista pusta to:
    if not data_list:
        print(Fore.YELLOW + "Brak danych do wyświetlenia.")
        return

    headers = list(headers_map.keys())#naglowki kolumn
    attrs = list(headers_map.values())#atrybuty

    col_widths = {header: len(header) for header in headers}#szerokosc tyle co naglowek
    for item in data_list:
        for header, attr in headers_map.items():#dla kazdego naglowka odpowiadajacy mu atrybut
            if callable(attr):#callable sprawdzam czy moge wywolac jako funkcje
                value = str(attr(item))#zamieniam na stringa
            else:
                value = item.get(attr, "N/A") if isinstance(item, dict) else getattr(item, attr, "N/A")#jesli item to slownik to pobieramy wartosc kucza
            col_widths[header] = max(col_widths[header], len(str(value)))

    print(Fore.CYAN + f"\n--- {title} ---")

    header_str = " | ".join(f"{header:<{col_widths[header]}}" for header in headers)#lista naglowkow
    print(Fore.GREEN + header_str)
    print("-" * len(header_str))#robi - na szerokosc naglowka

    for item in data_list:
        row_values = []#przechowuje wartosci kolumn
        for header, attr in headers_map.items():
            if callable(attr):#callable sprawdzam czy moge wywolac jako funkcje
                value = str(attr(item))#zamieniam na stringa
            else:
                value = item.get(attr, "N/A") if isinstance(item, dict) else getattr(item, attr, "N/A")#jesli item tto slownik to pobieram wartosc klucza
            row_values.append(f"{str(value):<{col_widths[header]}}")#dodaje
        print(" | ".join(row_values))
    print()

def display_menu(role):
    print(Fore.CYAN + Style.BRIGHT + "\n--- System Zarządzania Hotelem ---")
    if role == "administrator":
        print(Fore.YELLOW + "1. Zarządzaj Pokojami")
        print(Fore.YELLOW + "2. Zarządzaj Gośćmi")
        print(Fore.YELLOW + "3. Zarządzaj Rezerwacjami")
        print(Fore.YELLOW + "4. Zarządzaj Płatnościami i Fakturami")
        print(Fore.YELLOW + "5. Zarządzaj Sprzątaniem")
        print(Fore.YELLOW + "6. Zarządzaj Rabatami")
        print(Fore.YELLOW + "7. Zarządzaj Użytkownikami")
        print(Fore.YELLOW + "8. Generuj Raporty")
        print(Fore.YELLOW + "9. Wyjdź")
    elif role == "recepcjonista":
        print(Fore.YELLOW + "1. Zarządzaj Pokojami")
        print(Fore.YELLOW + "2. Zarządzaj Gośćmi")
        print(Fore.YELLOW + "3. Zarządzaj Rezerwacjami")
        print(Fore.YELLOW + "4. Zarządzaj Płatnościami i Fakturami")
        print(Fore.YELLOW + "5. Zarządzaj Sprzątaniem")
        print(Fore.YELLOW + "6. Zarządzaj Rabatami")
        print(Fore.YELLOW + "7. Generuj Raporty")
        print(Fore.YELLOW + "8. Wyjdź")
    elif role == "pokojówka":
        print(Fore.YELLOW + "1. Zarządzaj Sprzątaniem")
        print(Fore.YELLOW + "2. Wyjdź")
    else:
        print(Fore.RED + "Nieznana rola użytkownika.")
    print(Fore.CYAN + "-----------------------------------")

def manage_rooms_menu(room_service: RoomService, current_user: User):
    logger.info(f"Użytkownik {current_user.username} wchodzi do menu zarządzania pokojami.")
    if not current_user.has_permission("recepcjonista"):
        print(Fore.RED + "Brak uprawnień do zarządzania pokojami.")
        logger.warning(f"Użytkownik {current_user.username} próbował uzyskać dostęp do zarządzania pokojami bez uprawnień.")
        input("Naciśnij Enter, aby kontynuować...")
        return
    while True:
        print(Fore.CYAN + Style.BRIGHT + "\n--- Zarządzanie Pokojami ---")
        print(Fore.YELLOW + "1. Dodaj Pokój")
        print(Fore.YELLOW + "2. Wyświetl Wszystkie Pokoje")
        print(Fore.YELLOW + "3. Edytuj Pokój")
        print(Fore.YELLOW + "4. Usuń Pokój")
        print(Fore.YELLOW + "5. Zmień Status Pokoju")
        print(Fore.YELLOW + "6. Znajdź Dostępne Pokoje")
        print(Fore.YELLOW + "7. Szukaj Pokoi (zaawansowane filtrowanie)")
        print(Fore.YELLOW + "8. Sortuj Pokoje")
        print(Fore.YELLOW + "9. Powrót do Głównego Menu")
        choice = input(Fore.GREEN + "Wprowadź swój wybór: ")

        if choice == '1':
            if not current_user.has_permission("recepcjonista"):
                print(Fore.RED + "Brak uprawnień do dodawania pokoi.")
                logger.warning(f"Użytkownik {current_user.username} próbował dodać pokój bez uprawnień.")
                continue
            print(Fore.CYAN + "\n--- Dodaj Nowy Pokój ---")
            number = input("Wprowadź numer pokoju: ")
            if room_service.get_room(number):
                print(Fore.RED + "Pokój o tym numerze już istnieje.")
                logger.warning(f"Próba dodania istniejącego pokoju: {number}")
                continue
            try:
                floor = int(input("Wprowadź piętro: "))
                room_type = get_numerical_choice(ROOM_TYPES, "Wybierz typ pokoju:")
                if not room_type:
                    print(Fore.RED + "Typ pokoju jest wymagany. Anulowano dodawanie pokoju.")
                    continue
                price = float(input("Wprowadź cenę za dobę: "))
                amenities_str = input("Wprowadź udogodnienia (oddzielone przecinkami, np. TV,Wi-Fi): ")
                amenities = [a.strip() for a in amenities_str.split(',') if a.strip()]
                room_service.add_room(number, floor, room_type, price, amenities)
                logger.info(f"Dodano nowy pokój: {number}")
            except ValueError as e:
                print(Fore.RED + "Nieprawidłowe dane. Proszę wprowadzić poprawne liczby dla piętra i ceny.")
                logger.error(f"Błąd podczas dodawania pokoju (ValueError): {e}")

        elif choice == '2':
            all_rooms = room_service.list_all_rooms()
            display_table(all_rooms, {"Numer Pokoju": "number", "Piętro": "floor", "Typ": "room_type", "Cena": "price", "Udogodnienia": "amenities", "Status": "status"}, "Wszystkie Pokoje")
            logger.info("Wyświetlono wszystkie pokoje.")

        elif choice == '3':
            print(Fore.CYAN + "\n--- Edytuj Pokój ---")
            number = input("Wprowadź numer pokoju do edycji: ")
            room = room_service.get_room(number)
            if room:
                print(f"Obecne dane dla Pokoju {number}")
                kwargs = {}
                try:
                    new_floor = input(f"Wprowadź nowe piętro (obecne: {room.floor}, pozostaw puste, aby zachować): ")
                    if new_floor: kwargs['floor'] = int(new_floor)
                    new_type = get_numerical_choice(ROOM_TYPES, f"Wybierz nowy typ pokoju (obecny: {room.room_type}):", allow_empty=True)
                    if new_type is not None: kwargs['room_type'] = new_type
                    new_price = input(f"Wprowadź nową cenę (obecna: {room.price}, pozostaw puste, aby zachować): ")
                    if new_price: kwargs['price'] = float(new_price)
                    new_amenities_str = input(f"Wprowadź nowe udogodnienia (obecne: {', '.join(room.amenities)}, oddzielone przecinkami, pozostaw puste, aby zachować): ")
                    if new_amenities_str: kwargs['amenities'] = [a.strip() for a in new_amenities_str.split(',') if a.strip()]

                    if kwargs:
                        room_service.update_room(number, **kwargs)
                        logger.info(f"Zaktualizowano pokój: {number}")
                    else:
                        print(Fore.YELLOW + "Nie określono żadnych zmian.")
                        logger.info(f"Brak zmian dla pokoju {number}.")
                except ValueError as e:
                    print(Fore.RED + "Nieprawidłowe dane. Proszę wprowadzić poprawne liczby dla piętra i ceny.")
                    logger.error(f"Błąd podczas edycji pokoju (ValueError): {e}")
            else:
                print(Fore.RED + f"Pokój {number} nie znaleziono.")
                logger.warning(f"Próba edycji nieistniejącego pokoju: {number}")
        
        elif choice == '4':
            if not current_user.has_permission("administrator"):
                print(Fore.RED + "Brak uprawnień do usuwania pokoi.")
                logger.warning(f"Użytkownik {current_user.username} próbował usunąć pokój bez uprawnień.")
                continue
            print(Fore.CYAN + "\n--- Usuń Pokój ---")
            number = input("Wprowadź numer pokoju do usunięcia: ")
            room_service.delete_room(number)
            logger.info(f"Próba usunięcia pokoju: {number}")

        elif choice == '5':
            if not current_user.has_permission("recepcjonista"):
                print(Fore.RED + "Brak uprawnień do zmiany statusu pokoju.")
                logger.warning(f"Użytkownik {current_user.username} próbował zmienić status pokoju bez uprawnień.")
                continue
            print(Fore.CYAN + "\n--- Zmień Status Pokoju ---")
            number = input("Podaj numer pokoju: ")
            status_options = ["dostępny", "zajęty", "sprzątanie", "niedostępny"]
            new_status = get_numerical_choice(status_options, "Wybierz nowy status:")
            if not new_status:
                print(Fore.RED + "Zmiana statusu anulowana.")
                continue
            room_service.update_room_status(number, new_status)

        elif choice == '6':
            available_rooms = room_service.find_available_rooms()
            display_table(available_rooms, {"Numer Pokoju": "number", "Piętro": "floor", "Typ": "room_type", "Cena": "price", "Udogodnienia": "amenities", "Status": "status"}, "Dostępne Pokoje")
            logger.info("Wyświetlono dostępne pokoje.")

        elif choice == '7':
            print(Fore.CYAN + "\n--- Szukaj Pokoi ---")
            room_type = get_numerical_choice(ROOM_TYPES, "Wybierz typ pokoju (pozostaw puste, aby pominąć):", allow_empty=True)
            min_price_str = input("Wprowadź minimalną cenę (pozostaw puste, aby pominąć): ")
            max_price_str = input("Wprowadź maksymalną cenę (pozostaw puste, aby pominąć): ")
            amenity = input("Wprowadź udogodnienie (pozostaw puste, aby pominąć): ")
            status_pl = get_numerical_choice(ROOM_STATUSES, "Wybierz status pokoju (pozostaw puste, aby pominąć):", allow_empty=True)
            status_en = ROOM_STATUS_MAPPING.get(status_pl) if status_pl else None

            min_price = float(min_price_str) if min_price_str else None
            max_price = float(max_price_str) if max_price_str else None

            found_rooms = room_service.search_rooms(
                room_type=room_type,
                min_price=min_price,
                max_price=max_price,
                amenity=amenity if amenity else None,
                status=status_en
            )
            display_table(found_rooms, {"Numer Pokoju": "number", "Piętro": "floor", "Typ": "room_type", "Cena": "price", "Udogodnienia": "amenities", "Status": "status"}, "Znalezione Pokoje")
            logger.info("Wykonano wyszukiwanie pokoi.")

        elif choice == '8':
            print(Fore.CYAN + "\n--- Sortuj Pokoje ---")
            sort_options = {
                "number": "Numer pokoju",
                "floor": "Piętro",
                "room_type": "Typ pokoju",
                "price": "Cena",
                "status": "Status"
            }
            sort_by = get_numerical_choice(list(sort_options.values()), "Sortuj według:")
            if not sort_by:
                print(Fore.RED + "Sortowanie anulowane. Wybierz opcję sortowania.")
                continue
            sort_by = next(key for key, value in sort_options.items() if value == sort_by)
            reverse_str = input("Kolejność malejąca? (tak/nie): ").lower()
            reverse = True if reverse_str == 'tak' else False
            all_rooms = room_service.list_all_rooms()
            sorted_rooms = room_service.sort_rooms(all_rooms, sort_by, reverse)
            if sorted_rooms:
                display_table(sorted_rooms, {"Numer Pokoju": "number", "Piętro": "floor", "Typ": "room_type", "Cena": "price", "Udogodnienia": "amenities", "Status": "status"}, "Posortowane Pokoje")

        elif choice == '9':
            break
        else:
            print(Fore.RED + "Nieprawidłowy wybór. Spróbuj ponownie.")
                
def manage_guests_menu(guest_service: GuestService, current_user: User):
    logger.info(f"Użytkownik {current_user.username} wchodzi do menu zarządzania gośćmi.")
    if not current_user.has_permission("recepcjonista"):
        print(Fore.RED + "Brak uprawnień do zarządzania gośćmi.")
        logger.warning(f"Użytkownik {current_user.username} próbował uzyskać dostęp do zarządzania gośćmi bez uprawnień.")
        input("Naciśnij Enter, aby kontynuować...")
        return
    while True:
        print(Fore.CYAN + Style.BRIGHT + "\n--- Zarządzanie Gośćmi ---")
        print(Fore.YELLOW + "1. Dodaj Gościa")
        print(Fore.YELLOW + "2. Wyświetl Wszystkich Gości")
        print(Fore.YELLOW + "3. Edytuj Gościa")
        print(Fore.YELLOW + "4. Usuń Gościa")
        print(Fore.YELLOW + "5. Dodaj Zapis Pobytu do Gościa")
        print(Fore.YELLOW + "6. Zaktualizuj Poziom Lojalności Gościa")
        print(Fore.YELLOW + "7. Szukaj Gości")
        print(Fore.YELLOW + "8. Sortuj Gości")
        print(Fore.YELLOW + "9. Powrót do Głównego Menu")
        choice = input(Fore.GREEN + "Wprowadź swój wybór: ")

        if choice == '1':
            print(Fore.CYAN + "\n--- Dodaj Nowego Gościa ---")
            guest_id = input("Wprowadź ID gościa:")
            first_name = input("Wprowadź imię gościa: ")
            last_name = input("Wprowadź nazwisko gościa: ")
            id_document = input("Wprowadź numer dokumentu tożsamości (np. paszport/dowód): ")
            email = input("Wprowadź adres e-mail (opcjonalnie): ")
            phone = input("Wprowadź numer telefonu (opcjonalnie): ")
            contact_info = {}
            if email: contact_info["email"] = email
            if phone: contact_info["phone"] = phone

            is_vip = input("Czy gość jest VIP-em? (tak/nie): ").lower() == 'tak'
            is_loyal = input("Czy gość jest lojalnym klientem? (tak/nie): ").lower() == 'tak'
            
            preferences_str = input("Wprowadź preferencje (oddzielone przecinkami, np. poduszki antyalergiczne, cichy pokój): ")
            preferences = [p.strip() for p in preferences_str.split(',') if p.strip()]

            guest_service.add_guest(guest_id, first_name, last_name, id_document, contact_info, is_vip, is_loyal, preferences)

        elif choice == '2':     
            all_guests = guest_service.list_all_guests()
            display_table(all_guests, {"ID Gościa": "guest_id", "Imię": "first_name", "Nazwisko": "last_name", "Dokument": "id_document", "Kontakt": "contact_info", "VIP": "is_vip", "Lojalny": "is_loyal_customer", "Poziom Lojalności": "loyalty_tier"}, "Wszyscy Goście")

        elif choice == '3':
            print(Fore.CYAN + "\n--- Edytuj Gościa ---")
            guest_id = input("Wprowadź ID gościa do edycji: ")
            guest = guest_service.get_guest(guest_id)
            if guest:
                print(f"Obecne dane dla Gościa {guest_id}: {guest}")
                kwargs = {}
                new_first_name = input(f"Wprowadź nowe imię (obecne: {guest.first_name}, pozostaw puste, aby zachować): ")
                if new_first_name: kwargs['first_name'] = new_first_name
                new_last_name = input(f"Wprowadź nowe nazwisko (obecne: {guest.last_name}, pozostaw puste, aby zachować): ")
                if new_last_name: kwargs['last_name'] = new_last_name
                new_id_document = input(f"Wprowadź nowy numer dokumentu (obecny: {guest.id_document}, pozostaw puste, aby zachować): ")
                if new_id_document: kwargs['id_document'] = new_id_document

                current_contact_info = guest.contact_info.copy()
                new_email = input(f"Wprowadź nowy e-mail (obecny: {current_contact_info.get('email','N/A')}, pozostaw puste, aby zachować): ")
                if new_email: current_contact_info['email'] = new_email
                new_phone = input(f"Wprowadź nowy telefon (obecny: {current_contact_info.get('phone','N/A')}, pozostaw puste, aby zachować): ")
                if new_phone: current_contact_info['phone'] = new_phone
                kwargs['contact_info'] = current_contact_info

                new_is_vip = input(f"Czy gość jest nowym VIP-em? (obecnie: {guest.is_vip}, tak/nie, pozostaw puste, aby zachować): ")
                if new_is_vip: kwargs['is_vip'] = new_is_vip.lower() == 'tak'
                new_is_loyal = input(f"Czy gość jest nowym lojalnym klientem? (obecnie: {guest.is_loyal_customer}, tak/nie, pozostaw puste, aby zachować): ")
                if new_is_loyal: kwargs['is_loyal_customer'] = new_is_loyal.lower() == 'tak'

                new_preferences_str = input(f"Wprowadź nowe preferencje (obecne: {', '.join(guest.preferences)}, oddzielone przecinkami, pozostaw puste, aby zachować): ")
                if new_preferences_str: kwargs['preferences'] = [p.strip() for p in new_preferences_str.split(',') if p.strip()]

                if kwargs:
                    guest_service.update_guest(guest_id, **kwargs)
                else:
                    print(Fore.YELLOW + "Nie określono żadnych zmian.")
            else:
                print(Fore.RED + f"Gość {guest_id} nie znaleziono.")

        elif choice == '4':
            print(Fore.CYAN + "\n--- Usuń Gościa ---")
            guest_id = input("Wprowadź ID gościa do usunięcia: ")
            guest_service.delete_guest(guest_id)

        elif choice == '5':
            print(Fore.CYAN + "\n--- Dodaj Zapis Pobytu ---")
            guest_id = input("Wprowadź ID gościa: ")
            room_number = input("Wprowadź numer pokoju pobytu: ")
            check_in_date = input("Wprowadź datę zameldowania (RRRR-MM-DD): ")
            check_out_date = input("Wprowadź datę wymeldowania (RRRR-MM-DD): ")
            stay_details = {
                "room_number": room_number,
                "check_in": check_in_date,
                "check_out": check_out_date
            }
            guest_service.add_stay_record_to_guest(guest_id, stay_details)

        elif choice == '6':
            print(Fore.CYAN + "\n--- Zaktualizuj Poziom Lojalności ---")
            guest_id = input(Fore.GREEN + "Wprowadź ID gościa do aktualizacji poziomu lojalności: ")
            guest = guest_service.get_guest(guest_id)
            if guest:
                print(Fore.YELLOW + f"\nObecny poziom lojalności gościa: {guest.loyalty_tier}")
                # print(Fore.YELLOW + "\nDostępne poziomy lojalności:")
                # for i, tier in enumerate(GUEST_LOYALTY_TIERS, 1):
                #     print(Fore.YELLOW + f"{i}. {tier}")
                new_tier = get_numerical_choice(GUEST_LOYALTY_TIERS, Fore.GREEN + "Wybierz nowy poziom lojalności:")
                if new_tier:
                    guest_service.update_guest_loyalty_tier(guest_id, new_tier)
                    print(Fore.GREEN + f"Poziom lojalności gościa {guest_id} został zaktualizowany na {new_tier}.")
                else:
                    print(Fore.RED + "Nie wybrano nowego poziomu lojalności.")
            else:
                print(Fore.RED + f"Gość {guest_id} nie znaleziono.")

        elif choice == '7':
            print(Fore.CYAN + "\n--- Szukaj Gości ---")
            search_params = {}
            guest_id_search = input("Wprowadź ID gościa do wyszukania (pozostaw puste, aby pominąć): ")
            if guest_id_search: search_params['guest_id'] = guest_id_search
            first_name_search = input("Wprowadź imię do wyszukania (pozostaw puste, aby pominąć): ")
            if first_name_search: search_params['first_name'] = first_name_search
            last_name_search = input("Wprowadź nazwisko do wyszukania (pozostaw puste, aby pominąć): ")
            if last_name_search: search_params['last_name'] = last_name_search
            is_vip_search = input("Szukaj VIP-ów? (tak/nie/wszystkie): ").lower()
            if is_vip_search == 'tak': search_params['is_vip'] = True
            elif is_vip_search == 'nie': search_params['is_vip'] = False
            is_loyal_search = input("Szukaj lojalnych klientów? (tak/nie/wszystkie): ").lower()
            if is_loyal_search == 'tak': search_params['is_loyal_customer'] = True
            elif is_loyal_search == 'nie': search_params['is_loyal_customer'] = False
            loyalty_tier_search = get_numerical_choice(GUEST_LOYALTY_TIERS, "Szukaj po poziomie lojalności (pozostaw puste, aby pominąć):", allow_empty=True)
            if loyalty_tier_search: search_params['loyalty_tier'] = loyalty_tier_search
            contact_info_search = input("Wprowadź część danych kontaktowych (email/telefon, pozostaw puste, aby pominąć): ")
            if contact_info_search: search_params['contact_info'] = contact_info_search

            found_guests = guest_service.search_guests(**search_params)
            display_table(found_guests, {"ID Gościa": "guest_id", "Imię": "first_name", "Nazwisko": "last_name", "Poziom Lojalności": "loyalty_tier"}, "Znalezione Goście")
                              
        elif choice == '8':
            print(Fore.CYAN + "\n--- Sortuj Gości ---")
            sort_by_options = {
                "guest_id": "ID Gościa",
                "first_name": "Imię",
                "last_name": "Nazwisko",
                "is_vip": "Status VIP",
                "is_loyal_customer": "Status Lojalnego Klienta",
                "loyalty_tier": "Poziom Lojalności"
            }
            sort_by_choice = get_numerical_choice(list(sort_by_options.values()), "Sortuj gości według:")
            if not sort_by_choice: continue

            sort_by_key = next(key for key, value in sort_by_options.items() if value == sort_by_choice)
            reverse_sort = input("Odwróć kolejność? (tak/nie): ").lower() == 'tak'
            all_guests = guest_service.list_all_guests()
            sorted_guests = guest_service.sort_guests(all_guests, sort_by_key, reverse_sort)
            display_table(sorted_guests, {"ID Gościa": "guest_id", "Imię": "first_name", "Nazwisko": "last_name", "Poziom Lojalności": "loyalty_tier"}, f"Posortowani Goście według {sort_by_choice}")

        elif choice == '9':
            logger.info(f"Użytkownik {current_user.username} opuszcza menu zarządzania gośćmi.")
            break
        else:
            print(Fore.RED + "Nieprawidłowy wybór. Proszę spróbować ponownie.")
            logger.warning(f"Nieprawidłowy wybór w menu gości: {choice}")

def manage_reservations_menu(reservation_service: ReservationService, room_service: RoomService, guest_service: GuestService, payment_service: PaymentService, current_user: User):
    logger.info(f"Użytkownik {current_user.username} wchodzi do menu zarządzania rezerwacjami.")
    if not current_user.has_permission("recepcjonista"):
        print(Fore.RED + "Brak uprawnień do zarządzania rezerwacjami.")
        logger.warning(f"Użytkownik {current_user.username} próbował uzyskać dostęp do zarządzania rezerwacjami bez uprawnień.")
        input("Naciśnij Enter, aby kontynuować...")
        return
    while True:
        print(Fore.CYAN + Style.BRIGHT + "\n--- Zarządzanie Rezerwacjami ---")
        print(Fore.YELLOW + "1. Utwórz Rezerwację")
        print(Fore.YELLOW + "2. Wyświetl Wszystkie Rezerwacje")
        print(Fore.YELLOW + "3. Edytuj Rezerwację")
        print(Fore.YELLOW + "4. Anuluj Rezerwację")
        print(Fore.YELLOW + "5. Zameldowanie Gościa")
        print(Fore.YELLOW + "6. Wymeldowanie Gościa")
        print(Fore.YELLOW + "7. Sprawdź Dostępność Pokoju")
        print(Fore.YELLOW + "8. Szukaj Rezerwacji")
        print(Fore.YELLOW + "9. Sortuj Rezerwacje")
        print(Fore.YELLOW + "10. Powrót do Głównego Menu")
        choice = input(Fore.GREEN + "Wprowadź swój wybór: ")
        
        if choice == '1':
            print(Fore.CYAN + "\n--- Utwórz Nową Rezerwację ---")
            guest_id = input("Wprowadź ID gościa:")
            room_number = input("Wprowadź numer pokoju: ")
            check_in_date_str = input("Wprowadź datę zameldowania (RRRR-MM-DD): ")
            check_out_date_str = input("Wprowadź datę wymeldowania (RRRR-MM-DD): ")
            discount_code = input("Wprowadź kod rabatowy (opcjonalnie, pozostaw puste, aby pominąć): ")

            reservation_service.create_reservation(guest_id, room_number, check_in_date_str, check_out_date_str, discount_code if discount_code else None)

        elif choice == '2':
            all_reservations = reservation_service.list_all_reservations()
            def get_discount_code(res):
                if hasattr(res, 'applied_discount_id') and res.applied_discount_id:
                    discount = discount_service.get_discount(res.applied_discount_id)
                    return discount.code if discount else res.applied_discount_id
                return "N/A"
            display_table(all_reservations, {
                "ID Rezerwacji": "reservation_id", 
                "ID Gościa": "guest_id", 
                "Numer Pokoju": "room_number", 
                "Zameldowanie": lambda x: x.check_in.strftime('%Y-%m-%d') if x.check_in else "N/A", 
                "Wymeldowanie": lambda x: x.check_out.strftime('%Y-%m-%d') if x.check_out else "N/A", 
                "Cena": "total_price", 
                "Status": lambda x: REVERSE_RESERVATION_STATUS_MAPPING.get(x.status, x.status), 
                "Status Płatności": lambda x: REVERSE_PAYMENT_STATUS_MAPPING.get(x.payment_status, x.payment_status), 
                "Rabat": get_discount_code
            }, "Wszystkie Rezerwacje")

        elif choice == '3':
            print(Fore.CYAN + "\n--- Edytuj Rezerwację ---")
            reservation_id = input("Wprowadź ID rezerwacji do edycji: ")
            reservation = reservation_service.get_reservation(reservation_id)
            if reservation:
                print(f"Obecne dane dla Rezerwacji {reservation_id}: {reservation}")
                kwargs = {}
                new_guest_id = input(f"Wprowadź nowe ID gościa (obecne: {reservation.guest_id}, pozostaw puste, aby zachować): ")
                if new_guest_id: kwargs['guest_id'] = new_guest_id
                new_room_number = input(f"Wprowadź nowy numer pokoju (obecny: {reservation.room_number}, pozostaw puste, aby zachować): ")
                if new_room_number: kwargs['room_number'] = new_room_number
                new_check_in = input(f"Wprowadź nową datę zameldowania (obecna: {reservation.check_in.strftime('%Y-%m-%d') if hasattr(reservation.check_in, 'strftime') else reservation.check_in}, RRRR-MM-DD, pozostaw puste, aby zachować): ")
                if new_check_in: kwargs['check_in_date'] = new_check_in
                new_check_out = input(f"Wprowadź nową datę wymeldowania (obecna: {reservation.check_out.strftime('%Y-%m-%d') if hasattr(reservation.check_out, 'strftime') else reservation.check_out}, RRRR-MM-DD, pozostaw puste, aby zachować): ")
                if new_check_out: kwargs['check_out_date'] = new_check_out
                new_total_price = input(f"Wprowadź nową całkowitą cenę (obecna: {reservation.total_price}, pozostaw puste, aby zachować): ")
                if new_total_price: kwargs['total_price'] = float(new_total_price)
                new_status_pl = get_numerical_choice(RESERVATION_STATUSES, f"Wybierz nowy status rezerwacji (obecny: {reservation.status}):", allow_empty=True)
                if new_status_pl: kwargs['status'] = RESERVATION_STATUS_MAPPING.get(new_status_pl)
                new_payment_status = input(f"Wprowadź nowy status płatności (obecny: {getattr(reservation, 'payment_status', 'N/A')}, np. pending, paid, partially_paid, pozostaw puste, aby zachować): ")
                if new_payment_status: kwargs['payment_status'] = new_payment_status
                new_discount_id = input(f"Wprowadź nowy ID rabatu (obecny: {getattr(reservation, 'applied_discount_id', 'N/A')}, pozostaw puste, aby zachować): ")
                if new_discount_id: kwargs['applied_discount_id'] = new_discount_id

                if kwargs:
                    reservation_service.update_reservation(reservation_id, **kwargs)
                else:
                    print(Fore.YELLOW + "Nie określono żadnych zmian.")
            else:
                print(Fore.RED + f"Rezerwacja {reservation_id} nie znaleziono.")

        elif choice == '4':
            print(Fore.CYAN + "\n--- Anuluj Rezerwację ---")
            reservation_id = input("Wprowadź ID rezerwacji do anulowania: ")
            charge_fee = input("Czy naliczyć opłatę za anulowanie? (tak/nie): ").lower() == 'tak'
            reservation_service.cancel_reservation(reservation_id, charge_fee)

        elif choice == '5':
            print(Fore.CYAN + "\n--- Zameldowanie Gościa ---")
            reservation_id = input("Wprowadź ID rezerwacji do zameldowania: ")
            reservation_service.check_in_guest(reservation_id)

        elif choice == '6':
            print(Fore.CYAN + "\n--- Wymeldowanie Gościa ---")
            reservation_id = input("Wprowadź ID rezerwacji do wymeldowania: ")
            room_cleaning = input("Czy pokój wymaga sprzątania? (tak/nie): ").lower() == 'tak'
            try:
                late_checkout_fee = float(input("Wprowadź opłatę za późne wymeldowanie (0 jeśli brak): "))
            except ValueError:
                print(Fore.RED + "Nieprawidłowa kwota. Ustawiono 0.")
                late_checkout_fee = 0.0
            reservation_service.check_out_guest(reservation_id, room_cleaning, late_checkout_fee)

        elif choice == '7':
            print(Fore.CYAN + "\n--- Sprawdź Dostępność Pokoju ---")
            room_number = input("Wprowadź numer pokoju: ")
            check_in_date_str = input("Wprowadź datę zameldowania (RRRR-MM-DD): ")
            check_out_date_str = input("Wprowadź datę wymeldowania (RRRR-MM-DD): ")
            if reservation_service.is_room_available(room_number, check_in_date_str, check_out_date_str):
                print(Fore.GREEN + f"Pokój {room_number} jest dostępny w podanym terminie.")
            else:
                print(Fore.RED + f"Pokój {room_number} jest niedostępny w podanym terminie lub nie istnieje.")

        elif choice == '8':
            print(Fore.CYAN + "\n--- Szukaj Rezerwacji ---")
            search_params = {}
            res_id_search = input("Wprowadź ID rezerwacji do wyszukania (pozostaw puste, aby pominąć): ")
            if res_id_search: search_params['reservation_id'] = res_id_search
            guest_id_search = input("Wprowadź ID gościa do wyszukania (pozostaw puste, aby pominąć): ")
            if guest_id_search: search_params['guest_id'] = guest_id_search
            room_number_search = input("Wprowadź numer pokoju do wyszukania (pozostaw puste, aby pominąć): ")
            if room_number_search: search_params['room_number'] = room_number_search
            status_search = get_numerical_choice(RESERVATION_STATUSES, "Wybierz status do wyszukania (pozostaw puste, aby pominąć):", allow_empty=True)
            if status_search: search_params['status'] = RESERVATION_STATUS_MAPPING.get(status_search)
            payment_status_search = get_numerical_choice(PAYMENT_STATUSES, "Wybierz status płatności do wyszukania (pozostaw puste, aby pominąć):", allow_empty=True)
            if payment_status_search: search_params['payment_status'] = PAYMENT_STATUS_MAPPING.get(PAYMENT_STATUSES[payment_status_search-1])
            
            print("Wprowadź zakres dat zameldowania (opcjonalnie):")
            check_in_start = input("Data początkowa (RRRR-MM-DD, pozostaw puste, aby pominąć): ")
            check_in_end = input("Data końcowa (RRRR-MM-DD, pozostaw puste, aby pominąć): ")
            if check_in_start or check_in_end:
                search_params['check_in_date_range'] = (check_in_start, check_in_end)

            found_reservations = reservation_service.search_reservations(**search_params)
            display_table(found_reservations, {
                "ID Rezerwacji": "reservation_id", 
                "ID Gościa": "guest_id", 
                "Numer Pokoju": "room_number", 
                "Zameldowanie": lambda x: x.check_in.strftime('%Y-%m-%d') if x.check_in else "N/A", 
                "Status": lambda x: REVERSE_RESERVATION_STATUS_MAPPING.get(x.status, x.status)
            }, "Znalezione Rezerwacje")

        elif choice == '9':
            print(Fore.CYAN + "\n--- Sortuj Rezerwacje ---")
            sort_by_options = {
                "reservation_id": "ID Rezerwacji",
                "guest_id": "ID Gościa",
                "room_number": "Numer Pokoju",
                "check_in_date": "Data Zameldowania",
                "check_out_date": "Data Wymeldowania",
                "total_price": "Cena Całkowita",
                "status": "Status",
                "payment_status": "Status Płatności"
            }
            
            print("Sortuj rezerwacje według:")
            for i, (key, value) in enumerate(sort_by_options.items(), 1):
                print(f"{i}. {value}")
            
            sort_by_choice = get_numerical_choice(list(sort_by_options.keys()), "Wybierz kryterium sortowania:", allow_empty=True)
            if not sort_by_choice: continue

            reverse_sort = input("Odwróć kolejność? (tak/nie): ").lower() == 'tak'
            all_reservations = reservation_service.list_all_reservations()
            sorted_reservations = reservation_service.sort_reservations(all_reservations, sort_by_choice, reverse_sort)
            display_table(sorted_reservations, {
                "ID Rezerwacji": "reservation_id", 
                "ID Gościa": "guest_id", 
                "Numer Pokoju": "room_number", 
                "Zameldowanie": lambda x: x.check_in.strftime('%Y-%m-%d') if x.check_in else "N/A", 
                "Wymeldowanie": lambda x: x.check_out.strftime('%Y-%m-%d') if x.check_out else "N/A", 
                "Cena": "total_price", 
                "Status": lambda x: REVERSE_RESERVATION_STATUS_MAPPING.get(x.status, x.status), 
                "Status Płatności": lambda x: REVERSE_PAYMENT_STATUS_MAPPING.get(x.payment_status, x.payment_status), 
                "Rabat": "applied_discount_id"
            }, "Posortowane Rezerwacje")

        elif choice == '10':
            logger.info(f"Użytkownik {current_user.username} opuszcza menu zarządzania rezerwacjami.")
            break
        else:
            print(Fore.RED + "Nieprawidłowy wybór. Proszę spróbować ponownie.")
            logger.warning(f"Nieprawidłowy wybór w menu rezerwacji: {choice}")

def manage_payments_menu(payment_service: PaymentService, current_user: User):
    logger.info(f"Użytkownik {current_user.username} wchodzi do menu zarządzania płatnościami.")
    if not current_user.has_permission("recepcjonista"):
        print(Fore.RED + "Brak uprawnień do zarządzania płatnościami.")
        logger.warning(f"Użytkownik {current_user.username} próbował uzyskać dostęp do zarządzania płatnościami bez uprawnień.")
        input("Naciśnij Enter, aby kontynuować...")
        return
    while True:
        print(Fore.CYAN + Style.BRIGHT + "\n--- Zarządzanie Płatnościami i Fakturami ---")
        print(Fore.YELLOW + "1. Zarejestruj Płatność")
        print(Fore.YELLOW + "2. Generuj Fakturę")
        print(Fore.YELLOW + "3. Wyświetl Wszystkie Płatności")
        print(Fore.YELLOW + "4. Wyświetl Wszystkie Faktury")
        print(Fore.YELLOW + "5. Wyświetl Nieuregulowane Faktury")
        print(Fore.YELLOW + "6. Wydrukuj Fakturę (do pliku/podglądu)")
        print(Fore.YELLOW + "7. Powrót do Głównego Menu")
        choice = input(Fore.GREEN + "Wprowadź swój wybór: ")

        if choice == '1':
            print(Fore.CYAN + "\n--- Zarejestruj Płatność ---")
            reservation_id = input("Wprowadź ID rezerwacji: ")
            try:
                amount = float(input("Wprowadź kwotę płatności: "))
                payment_method = get_numerical_choice(PAYMENT_METHODS, "Wybierz metodę płatności:")
                if not payment_method:
                    print(Fore.RED + "Metoda płatności jest wymagana. Anulowano rejestrację.")
                    continue
                payment_service.record_payment(reservation_id, amount, payment_method)
            except ValueError:
                print(Fore.RED + "Nieprawidłowa kwota. Proszę wprowadzić poprawną liczbę.")
                logger.error("Nieprawidłowa kwota płatności.")

        elif choice == '2':
            print(Fore.CYAN + "\n--- Generuj Fakturę ---")
            reservation_id = input("Wprowadź ID rezerwacji, dla której chcesz wygenerować fakturę: ")
            payment_service.generate_invoice(reservation_id)

        elif choice == '3':
            all_payments = payment_service.list_all_payments()
            display_table(all_payments, {"ID Płatności": "payment_id", "ID Rezerwacji": "reservation_id", "Kwota": "amount", "Data Płatności": "payment_date", "Metoda": "payment_method"}, "Wszystkie Płatności")

        elif choice == '4':
            all_invoices = payment_service.list_all_invoices()
            display_table(all_invoices, {
                "ID Faktury": "invoice_id", 
                "ID Rezerwacji": "reservation_id", 
                "ID Gościa": "guest_id", 
                "Data Wystawienia": "issue_date", 
                "Termin Płatności": "due_date", 
                "Suma": "total_amount", 
                "Zapłacono": "paid_amount", 
                "Status": lambda x: REVERSE_INVOICE_STATUS_MAPPING.get(x.status, x.status)
            }, "Wszystkie Faktury")

        elif choice == '5':
            outstanding_invoices = payment_service.get_outstanding_invoices()
            display_table(outstanding_invoices, {
                "ID Faktury": "invoice_id", 
                "ID Rezerwacji": "reservation_id", 
                "Suma": "total_amount", 
                "Zapłacono": "paid_amount", 
                "Status": lambda x: REVERSE_INVOICE_STATUS_MAPPING.get(x.status, x.status)
            }, "Nieuregulowane Faktury")
        
        elif choice == '6':
            print(Fore.CYAN + "\n--- Wydrukuj Fakturę ---")
            invoice_id = input("Wprowadź ID faktury do wydrukowania: ")
            output_format = get_numerical_choice(["txt", "pdf"], "Wybierz format wyjściowy (1.txt, 2.pdf):")
            if output_format:
                payment_service.print_invoice(invoice_id, output_format)
            else:
                print(Fore.RED + "Format wyjściowy jest wymagany. Anulowano drukowanie.")

        elif choice == '7':
            logger.info(f"Użytkownik {current_user.username} opuszcza menu zarządzania płatnościami.")
            break
        else:
            print(Fore.RED + "Nieprawidłowy wybór. Proszę spróbować ponownie.")
            logger.warning(f"Nieprawidłowy wybór w menu płatności: {choice}")

def manage_housekeeping_menu(housekeeping_service: HousekeepingService, room_service: RoomService, current_user: User):
    logger.info(f"Użytkownik {current_user.username} wchodzi do menu zarządzania sprzątaniem.")
    if not current_user.has_permission("pokojówka"):
        print(Fore.RED + "Brak uprawnień do zarządzania sprzątaniem.")
        logger.warning(f"Użytkownik {current_user.username} próbował uzyskać dostęp do zarządzania sprzątaniem bez uprawnień.")
        input("Naciśnij Enter, aby kontynuować...")
        return
    while True:
        print(Fore.CYAN + Style.BRIGHT + "\n--- Zarządzanie Sprzątaniem ---")
        print(Fore.YELLOW + "1. Utwórz Zadanie Sprzątania")
        print(Fore.YELLOW + "2. Zmień Status Zadania")
        print(Fore.YELLOW + "3. Przypisz Zadanie")
        print(Fore.YELLOW + "4. Usuń Zadanie")
        print(Fore.YELLOW + "5. Wyświetl Wszystkie Zadania")
        print(Fore.YELLOW + "6. Wyświetl Harmonogram Dzienny")
        print(Fore.YELLOW + "7. Powrót do Głównego Menu")
        choice = input(Fore.GREEN + "Wprowadź swój wybór: ")

        if choice == '1':
            print(Fore.CYAN + "\n--- Utwórz Zadanie Sprzątania ---")
            room_number = input("Wprowadź numer pokoju: ")
            room = room_service.get_room(room_number)
            if not room:
                print(Fore.RED + "Pokój nie znaleziono. Nie można utworzyć zadania.")
                continue

            assigned_to = input("Wprowadź osobę odpowiedzialną za zadanie: ")
            due_date_str = input("Wprowadź termin wykonania (RRRR-MM-DD): ")
            notes = input("Wprowadź uwagi (opcjonalnie): ")
            housekeeping_service.create_task(room_number, assigned_to, due_date_str, notes)

        elif choice == '2':
            print(Fore.CYAN + "\n--- Zmień Status Zadania Sprzątania ---")
            task_id = input(Fore.GREEN + "Wprowadź ID zadania do zmiany statusu: ")
            print(Fore.YELLOW + "\nDostępne statusy:")
            for i, status in enumerate(HOUSEKEEPING_TASK_STATUSES, 1):
                print(Fore.YELLOW + f"{i}. {status}")
            new_status_pl = get_numerical_choice(HOUSEKEEPING_TASK_STATUSES, Fore.GREEN + "Wybierz nowy status:")
            if not new_status_pl:
                print(Fore.RED + "Status jest wymagany. Anulowano zmianę statusu.")
                continue
            new_status_en = HOUSEKEEPING_STATUS_MAPPING.get(new_status_pl)
            if new_status_en:
                completed_date_str = None
                if new_status_en == "completed":
                    completed_date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                housekeeping_service.update_task_status(task_id, new_status_en, current_user.role, completed_date_str)
                print(Fore.GREEN + f"Status zadania {task_id} został zmieniony na {new_status_pl}.")
            else:
                print(Fore.RED + "Nieprawidłowy status. Spróbuj ponownie.")

        elif choice == '3':
            print(Fore.CYAN + "\n--- Przypisz Zadanie Sprzątania ---")
            task_id = input("Wprowadź ID zadania do przypisania: ")
            assigned_to = input("Wprowadź osobę, której przypisać zadanie: ")
            housekeeping_service.assign_task(task_id, assigned_to)

        elif choice == '4':
            print(Fore.CYAN + "\n--- Usuń Zadanie Sprzątania ---")
            task_id = input("Wprowadź ID zadania do usunięcia: ")
            housekeeping_service.delete_task(task_id)

        elif choice == '5':
            all_tasks = housekeeping_service.list_all_tasks()
            display_table(all_tasks, {
                "ID Zadania": "task_id", 
                "Numer Pokoju": "room_number", 
                "Przypisane do": "assigned_to", 
                "Termin": "due_date", 
                "Status": lambda x: REVERSE_HOUSEKEEPING_STATUS_MAPPING.get(x.status, x.status), 
                "Notatki": "notes"
            }, "Wszystkie Zadania Sprzątania")

        elif choice == '6':
            print(Fore.CYAN + "\n--- Harmonogram Dzienny Sprzątania ---")
            date_str = input("Wprowadź datę (RRRR-MM-DD) dla harmonogramu dziennego: ")
            daily_schedule = housekeeping_service.get_daily_schedule(date_str)
            display_table(daily_schedule, {
                "ID Zadania": "task_id", 
                "Numer Pokoju": "room_number", 
                "Przypisane do": "assigned_to", 
                "Termin": "due_date", 
                "Status": lambda x: REVERSE_HOUSEKEEPING_STATUS_MAPPING.get(x.status, x.status), 
                "Notatki": "notes"
            }, f"Harmonogram Sprzątania na {date_str}")

        elif choice == '7':
            logger.info(f"Użytkownik {current_user.username} opuszcza menu zarządzania sprzątaniem.")
            break
        else:
            print(Fore.RED + "Nieprawidłowy wybór. Proszę spróbować ponownie.")
            logger.warning(f"Nieprawidłowy wybór w menu sprzątania: {choice}")

def manage_reports_menu(report_service: ReportService, room_service: RoomService, reservation_service: ReservationService, current_user: User):
    if not current_user.has_permission("recepcjonista"):
        print(Fore.RED + "Brak uprawnień do generowania raportów.")
        input("Naciśnij Enter, aby kontynuować...")
        return
    while True:
        print(Fore.CYAN + Style.BRIGHT + "\n--- Generowanie Raportów ---")
        print(Fore.YELLOW + "1. Raport Dziennego Obłożenia")
        print(Fore.YELLOW + "2. Raport Przychodów za Okres")
        print(Fore.YELLOW + "3. Raport Anulowanych Rezerwacji")
        print(Fore.YELLOW + "4. Raport Przyjazdów i Wyjazdów")
        print(Fore.YELLOW + "5. Raport Statystyk Gości")
        print(Fore.YELLOW + "6. Raport Zadań Sprzątania")
        print(Fore.YELLOW + "7. Wizualizuj Obłożenie Pokoi według Typu")
        print(Fore.YELLOW + "8. Eksportuj Raport do Pliku")
        print(Fore.YELLOW + "9. Powrót do Głównego Menu")
        choice = input(Fore.GREEN + "Wprowadź swój wybór: ")

        report_options = [
            "1. Raport Dziennego Obłożenia",
            "2. Raport Przychodów za Okres",
            "3. Raport Anulowanych Rezerwacji",
            "4. Raport Przyjazdów i Wyjazdów",
            "5. Raport Statystyk Gości",
            "6. Raport Zadań Sprzątania"
        ]

        structured_data = []
        report_content = None

        if choice == '1':
            date_str = input("Wprowadź datę dla raportu obłożenia (RRRR-MM-DD): ")
            report_content, structured_data = report_service.generate_occupancy_report(date_str)
            if not structured_data and not report_content:
                report_content = "Brak danych do wygenerowania raportu obłożenia."
            
            if report_content:
                print(report_content)
            
            if structured_data:
                # print(f"structured_data przed display_table: {structured_data}")
                headers = {
                    "Data": "Data",
                    "Numer Pokoju": "Numer Pokoju",
                    "Typ Pokoju": "Typ Pokoju",
                    "Status": "Status",
                    "ID Rezerwacji": "ID Rezerwacji",
                    "ID Gościa": "ID Gościa"
                }
                display_table(structured_data, headers, "Szczegóły Obłożenia")
            
            filename_base = f"raport_oblozenia_{date_str}"
            report_type_name = "Obłożenia"
        elif choice == '2':
            start_date_str = input("Wprowadź datę początkową (RRRR-MM-DD): ")
            end_date_str = input("Wprowadź datę końcową (RRRR-MM-DD): ")
            report_content, structured_data = report_service.generate_revenue_report(start_date_str, end_date_str)
            
            if not structured_data and not report_content:
                report_content = "Brak danych do wygenerowania raportu przychodów."

            if report_content:
                print(report_content)
            
            if structured_data:
                headers = {
                    "Data": "Data",
                    "ID Płatności": "ID Płatności",
                    "ID Rezerwacji": "ID Rezerwacji",
                    "Kwota Płatności": "Kwota Płatności",
                    "Metoda Płatności": "Metoda Płatności"
                }
                display_table(structured_data, headers, "Szczegóły Przychodów")

            filename_base = f"raport_przychodow_{start_date_str}_do_{end_date_str}"
            report_type_name = "Przychodów"
        elif choice == '3':
            start_date_str = input("Wprowadź datę początkową (RRRR-MM-DD, opcjonalnie): ")
            end_date_str = input("Wprowadź datę końcową (RRRR-MM-DD, opcjonalnie): ")
            report_content, structured_data = report_service.generate_cancelled_reservations_report(start_date_str, end_date_str)
            
            if not structured_data and not report_content:
                report_content = "Brak danych do wygenerowania raportu anulowanych rezerwacji."

            if report_content:
                print(report_content)
            
            if structured_data:
                headers = {
                    "ID Rezerwacji": "ID Rezerwacji",
                    "ID Gościa": "ID Gościa",
                    "Numer Pokoju": "Numer Pokoju",
                    "Data Zameldowania (Pierwotna)": "Data Zameldowania (Pierwotna)",
                    "Data Wymeldowania (Pierwotna)": "Data Wymeldowania (Pierwotna)",
                    "Suma Rezerwacji": "Suma Rezerwacji"
                }
                display_table(structured_data, headers, "Szczegóły Anulowanych Rezerwacji")

            filename_base = "raport_anulowanych_rezerwacji"
            report_type_name = "Anulowanych Rezerwacji"
        elif choice == '4':
            date_str = input("Wprowadź datę dla raportu przyjazdów/wyjazdów (RRRR-MM-DD): ")
            report_content, arrivals, departures = report_service.generate_arrivals_departures_report(date_str)
            structured_data = arrivals + departures
            
            if not structured_data and not report_content:
                report_content = "Brak danych do wygenerowania raportu przyjazdów i wyjazdów."

            if report_content:
                print(report_content)
            
            if structured_data:
                headers = {
                    "Typ": "Typ",
                    "ID Rezerwacji": "ID Rezerwacji",
                    "ID Gościa": "ID Gościa",
                    "Numer Pokoju": "Numer Pokoju",
                    "Data": "Data"
                }
                display_table(structured_data, headers, "Szczegóły Przyjazdów i Wyjazdów")

            filename_base = f"raport_przyjazdow_wyjazdow_{date_str}"
            report_type_name = "Przyjazdów i Wyjazdów"
        elif choice == '5':
            report_content, structured_data = report_service.generate_guest_statistics_report()
            
            if not structured_data and not report_content:
                report_content = "Brak danych do wygenerowania raportu statystyk gości."

            if report_content:
                print(report_content)
            
            if structured_data:
                headers = {
                    "Typ Statystyki": "Typ Statystyki",
                    "Wartość": "Wartość"
                }
                display_table(structured_data, headers, "Szczegóły Statystyk Gości")

            filename_base = "raport_statystyk_gosci"
            report_type_name = "Statystyk Gości"
        elif choice == '6':
            report_content, structured_data = report_service.generate_housekeeping_report()
            filename_base = "raport_sprzatania"
            report_type_name = "Zadań Sprzątania"
            
            if report_content:
                print(report_content)
            
            if structured_data:
                # print(f"structured_data for housekeeping report: {structured_data}")
                headers = {
                    "ID Zadania": "task_id",
                    "Numer Pokoju": "room_number",
                    "Przypisane do": "assigned_to",
                    "Termin": "due_date",
                    "Status": "status",
                    "Notatki": "notes"
                }
                display_table(structured_data, headers, "Szczegóły Zadań Sprzątania")
        elif choice == '7':
            report_service.plot_occupancy_by_room_type(room_service.list_all_rooms()) 
        elif choice == '8':
            print(Fore.CYAN + "\n--- Eksportuj Raport do Pliku ---")
            print(Fore.YELLOW + "Który raport chcesz wyeksportować?")
            print(Fore.YELLOW + "1. Raport Dziennego Obłożenia")
            print(Fore.YELLOW + "2. Raport Przychodów za Okres")
            print(Fore.YELLOW + "3. Raport Anulowanych Rezerwacji")
            print(Fore.YELLOW + "4. Raport Przyjazdów i Wyjazdów")
            print(Fore.YELLOW + "5. Raport Statystyk Gości")
            print(Fore.YELLOW + "6. Raport Zadań Sprzątania")
            report_choice_num = input(Fore.GREEN + "Wprowadź wybór raportu do eksportu: ")
            if report_choice_num not in [str(i) for i in range(1, 7)]:
                print(Fore.RED + "Nieprawidłowy wybór raportu. Anulowano eksport.")
                continue
            report_choice = report_choice_num
            
            report_content_export = None
            structured_data_export = []
            filename_export_base = ""
            report_type_export_name = ""

            if report_choice == '1':
                date_str = input("Wprowadź datę dla raportu obłożenia (RRRR-MM-DD): ")
                report_content_export, structured_data_export = report_service.generate_occupancy_report(date_str)
                
                if not structured_data_export and not report_content_export:
                    report_content_export = "Brak danych do wygenerowania raportu obłożenia."

                filename_export_base = f"raport_oblozenia_{date_str}"
                report_type_export_name = "Obłożenia"
            elif report_choice == '2':
                start_date_str = input("Wprowadź datę początkową (RRRR-MM-DD): ")
                end_date_str = input("Wprowadź datę końcową (RRRR-MM-DD): ")
                report_content_export, structured_data_export = report_service.generate_revenue_report(start_date_str, end_date_str)
                
                if not structured_data_export and not report_content_export:
                    report_content_export = "Brak danych do wygenerowania raportu przychodów."

                filename_export_base = f"raport_przychodow_{start_date_str}_do_{end_date_str}"
                report_type_export_name = "Przychodów"
            elif report_choice == '3':
                start_date_str = input("Wprowadź datę początkową (RRRR-MM-DD, opcjonalnie): ")
                end_date_str = input("Wprowadź datę końcową (RRRR-MM-DD, opcjonalnie): ")
                report_content_export, structured_data_export = report_service.generate_cancelled_reservations_report(start_date_str, end_date_str)
                
                if not structured_data_export and not report_content_export:
                    report_content_export = "Brak danych do wygenerowania raportu anulowanych rezerwacji."

                if report_content_export:
                    print(report_content_export)
                
                if structured_data_export:
                    headers = {
                        "ID Rezerwacji": "ID Rezerwacji",
                        "ID Gościa": "ID Gościa",
                        "Numer Pokoju": "Numer Pokoju",
                        "Data Zameldowania (Pierwotna)": "Data Zameldowania (Pierwotna)",
                        "Data Wymeldowania (Pierwotna)": "Data Wymeldowania (Pierwotna)",
                        "Suma Rezerwacji": "Suma Rezerwacji"
                    }
                    display_table(structured_data_export, headers, "Szczegóły Anulowanych Rezerwacji")

                filename_export_base = "raport_anulowanych_rezerwacji"
                report_type_export_name = "Anulowanych Rezerwacji"
            elif report_choice == '4':
                date_str = input("Wprowadź datę dla raportu przyjazdów/wyjazdów (RRRR-MM-DD): ")
                report_content_export, arrivals, departures = report_service.generate_arrivals_departures_report(date_str)
                structured_data_export = arrivals + departures
                
                if not structured_data_export and not report_content_export:
                    report_content_export = "Brak danych do wygenerowania raportu przyjazdów i wyjazdów."

                filename_export_base = f"raport_przyjazdow_wyjazdow_{date_str}"
                report_type_export_name = "Przyjazdów i Wyjazdów"
            elif report_choice == '5':
                report_content_export, structured_data_export = report_service.generate_guest_statistics_report()
                
                if not structured_data_export and not report_content_export:
                    report_content_export = "Brak danych do wygenerowania raportu statystyk gości."

                if report_content_export:
                    print(report_content_export)
                
                if structured_data_export:
                    headers_export = {
                        "Typ Statystyki": "Typ Statystyki",
                        "Wartość": "Wartość"
                    }
                    display_table(structured_data_export, headers_export, "Szczegóły Statystyk Gości")

                filename_export_base = "raport_statystyk_gosci"
                report_type_export_name = "Statystyk Gości"
            elif report_choice == '6':
                report_content_export, structured_data_export = report_service.generate_housekeeping_report()
                filename_export_base = "raport_sprzatania"
                report_type_export_name = "Zadań Sprzątania"
                
                if report_content_export:
                    print(report_content_export)
                
                if structured_data_export:
                    headers = {
                        "ID Zadania": "task_id",
                        "Numer Pokoju": "room_number",
                        "Przypisane do": "assigned_to",
                        "Termin": "due_date",
                        "Status": "status",
                        "Notatki": "notes"
                    }
                    display_table(structured_data_export, headers, "Szczegóły Zadań Sprzątania")
            else:
                print(Fore.RED + "Nieprawidłowy wybór raportu.")
                continue

            if report_content_export:
                print(Fore.CYAN + "\n--- Wybierz Format Eksportu ---")
                print(Fore.YELLOW + "1. Plik tekstowy (.txt)")
                if structured_data_export: 
                    print(Fore.YELLOW + "2. CSV (.csv)")
                export_format_choice = input(Fore.GREEN + "Wprowadź swój wybór: ")

                if export_format_choice == '1':
                    report_service.export_report_to_file(report_content_export, f"{filename_export_base}.txt")
                elif export_format_choice == '2' and structured_data_export:
                    if report_choice == '5' and structured_data_export and structured_data_export[0] and isinstance(structured_data_export[0].get('Preferences'), list):
                        pref_data = structured_data_export[0].pop('Preferences') 
                        if pref_data: report_service.export_to_csv(pref_data, f"{filename_export_base}_preferencje.csv")
                        report_service.export_to_csv(structured_data_export, f"{filename_export_base}.csv")
                    else:
                        report_service.export_to_csv(structured_data_export, f"{filename_export_base}.csv")
                elif export_format_choice == '3' and structured_data_export:
                    if report_choice == '5' and structured_data_export and structured_data_export[0] and isinstance(structured_data_export[0].get('Preferences'), list):
                        pref_data = structured_data_export[0].pop('Preferences')
                        if pref_data: report_service.export_to_excel(pref_data, f"{filename_export_base}_preferencje.xlsx")
                        report_service.export_to_excel(structured_data_export, f"{filename_export_base}.xlsx")
                    else:
                        report_service.export_to_excel(structured_data_export, f"{filename_export_base}.xlsx")
                else:
                    print(Fore.RED + "Nieprawidłowy wybór formatu eksportu lub brak danych do eksportu w tym formacie.")

            else: 
                print(Fore.RED + "Nie można wygenerować raportu do eksportu.")

        elif choice == '9':
            break
        else:
            print(Fore.RED + "Nieprawidłowy wybór. Spróbuj ponownie.")

def manage_users_menu(user_service: UserService, current_user: User):
    if not current_user.has_permission("administrator"):
        print(Fore.RED + "Brak uprawnień do zarządzania użytkownikami.")
        input("Naciśnij Enter, aby kontynuować...")
        return

    while True:
        print(Fore.CYAN + Style.BRIGHT + "\n--- Zarządzanie Użytkownikami ---")
        print(Fore.YELLOW + "1. Dodaj Użytkownika")
        print(Fore.YELLOW + "2. Wyświetl Wszystkich Użytkowników")
        print(Fore.YELLOW + "3. Edytuj Użytkownika")
        print(Fore.YELLOW + "4. Usuń Użytkownika")
        print(Fore.YELLOW + "5. Powrót do Głównego Menu")
        choice = input(Fore.GREEN + "Wprowadź swój wybór: ")

        if choice == '1':
            print(Fore.CYAN + "\n--- Dodaj Nowego Użytkownika ---")
            username = input("Wprowadź nazwę użytkownika: ")
            password = input("Wprowadź hasło: ")
            role = input("Wprowadź rolę (administrator, recepcjonista, pokojówka): ").lower()
            employee_id = input("Wprowadź ID pracownika (opcjonalnie): ")
            user_service.add_user(username, password, role, employee_id if employee_id else None)

        elif choice == '2':
            all_users = user_service.list_all_users()
            display_table(all_users, {"Nazwa Użytkownika": "username", "Rola": "role", "ID Pracownika": "employee_id"}, "Wszyscy Użytkownicy")

        elif choice == '3':
            print(Fore.CYAN + "\n--- Edytuj Użytkownika ---")
            username = input("Wprowadź nazwę użytkownika do edycji: ")
            user = user_service.get_user_by_username(username)
            if user:
                print(f"Obecne dane dla Użytkownika {username}: {user}")
                kwargs = {}
                new_password = input(f"Wprowadź nowe hasło (pozostaw puste, aby zachować): ")
                if new_password: kwargs['password'] = new_password
                new_role = input(f"Wprowadź nową rolę (obecna: {user.role}, administrator/recepcjonista/pokojówka, pozostaw puste, aby zachować): ").lower()
                if new_role: kwargs['role'] = new_role
                new_employee_id = input(f"Wprowadź nowe ID pracownika (obecne: {user.employee_id}, pozostaw puste, aby zachować): ")
                if new_employee_id: kwargs['employee_id'] = new_employee_id

                if kwargs: user_service.update_user(username, **kwargs)
                else: print(Fore.YELLOW + "Nie określono żadnych zmian.")
            else:
                print(Fore.RED + f"Użytkownik {username} nie znaleziono.")

        elif choice == '4':
            print(Fore.CYAN + "\n--- Usuń Użytkownika ---")
            username = input("Wprowadź nazwę użytkownika do usunięcia: ")
            if username == current_user.username:
                print(Fore.RED + "Nie możesz usunąć aktualnie zalogowanego użytkownika.")
                continue
            user_service.delete_user(username)

        elif choice == '5':
            break
        else:
            print(Fore.RED + "Nieprawidłowy wybór. Spróbuj ponownie.")

def manage_discounts_menu(discount_service: DiscountService, current_user: User):
    if not current_user.has_permission("recepcjonista"):
        print(Fore.RED + "Brak uprawnień do zarządzania rabatami.")
        input("Naciśnij Enter, aby kontynuować...")
        return

    while True:
        print(Fore.CYAN + Style.BRIGHT + "\n--- Zarządzanie Rabatami ---")
        print(Fore.YELLOW + "1. Dodaj Rabat")
        print(Fore.YELLOW + "2. Wyświetl Wszystkie Rabaty")
        print(Fore.YELLOW + "3. Edytuj Rabat")
        print(Fore.YELLOW + "4. Usuń Rabat")
        # print(Fore.YELLOW + "5. Znajdź Obowiązujące Rabaty")
        print(Fore.YELLOW + "5. Powrót do Głównego Menu")
        choice = input(Fore.GREEN + "Wprowadź swój wybór: ")

        if choice == '1':
            print(Fore.CYAN + "\n--- Dodaj Nowy Rabat ---")
            code = input("Wprowadź kod rabatowy: ")
            percentage_str = input("Wprowadź procent zniżki (np. 10.0 dla 10%, pozostaw puste dla stałej kwoty): ")
            fixed_amount_str = input("Wprowadź stałą kwotę zniżki (pozostaw puste dla procentu): ")
            valid_from = input("Wprowadź datę rozpoczęcia ważności (RRRR-MM-DD, opcjonalnie): ")
            valid_to = input("Wprowadź datę zakończenia ważności (RRRR-MM-DD, opcjonalnie): ")
            min_stay_days_str = input("Wprowadź minimalną liczbę dni pobytu (0 jeśli brak wymogu): ")
            applicable_room_types = get_multiple_numerical_choices(ROOM_TYPES, "Wybierz typy pokoi, do których rabat ma zastosowanie (oddzielone przecinkami, opcjonalnie):", allow_empty=True)
            applicable_guest_ids_str = input("Wprowadź ID gości (oddzielone przecinkami, opcjonalnie): ")
            description = input("Wprowadź opis rabatu (opcjonalnie): ")

            percentage = float(percentage_str) if percentage_str else 0.0
            fixed_amount = float(fixed_amount_str) if fixed_amount_str else 0.0
            min_stay_days = int(min_stay_days_str) if min_stay_days_str else 0
            applicable_guest_ids = [g.strip() for g in applicable_guest_ids_str.split(',') if g.strip()] if applicable_guest_ids_str else None
            applicable_loyalty_tiers = get_multiple_numerical_choices(GUEST_LOYALTY_TIERS, "Wprowadź poziomy lojalności (Bronze, Silver, Gold, Platinum, oddzielone przecinkami, opcjonalnie): ", allow_empty=True)

            discount_service.add_discount(code, percentage, fixed_amount,
                                          valid_from if valid_from else None, valid_to if valid_to else None,
                                          min_stay_days, applicable_room_types, applicable_guest_ids, description, applicable_loyalty_tiers)

        elif choice == '2':
            all_discounts = discount_service.list_all_discounts()
            display_table(all_discounts, {"ID Rabatu": "discount_id", "Kod": "code", "Procent": "percentage", "Kwota Stała": "fixed_amount", "Ważny od": "valid_from", "Ważny do": "valid_to", "Min. Pobyt": "min_stay_days", "Typy Pokoi": "applicable_room_types", "ID Gości": "applicable_guest_ids", "Status": "is_active", "Poziomy Lojalności": "applicable_loyalty_tiers", "Opis": "description"}, "Wszystkie Rabaty")

        elif choice == '3':
            print(Fore.CYAN + "\n--- Edytuj Rabat ---")
            discount_code = input("Wprowadź kod rabatowy do edycji: ")
            discount = discount_service.get_discount(discount_code)
            if discount:
                print(f"Obecne dane dla Rabatu {discount_code}: {discount}")
                kwargs = {}
                new_percentage = input(f"Wprowadź nowy procent zniżki (obecny: {discount.percentage}, pozostaw puste, aby zachować): ")
                if new_percentage: kwargs['percentage'] = float(new_percentage)
                new_fixed_amount = input(f"Wprowadź nową stałą kwotę zniżki (obecna: {discount.fixed_amount}, pozostaw puste, aby zachować): ")
                if new_fixed_amount: kwargs['fixed_amount'] = float(new_fixed_amount)
                new_valid_from = input(f"Wprowadź nową datę rozpoczęcia ważności (obecna: {discount.valid_from}, RRRR-MM-DD, pozostaw puste, aby zachować): ")
                if new_valid_from: kwargs['valid_from'] = new_valid_from
                new_valid_to = input(f"Wprowadź nową datę zakończenia ważności (obecna: {discount.valid_to}, RRRR-MM-DD, pozostaw puste, aby zachować): ")
                if new_valid_to: kwargs['valid_to'] = new_valid_to
                new_min_stay_days = input(f"Wprowadź nową minimalną liczbę dni pobytu (obecna: {discount.min_stay_days}, pozostaw puste, aby zachować): ")
                if new_min_stay_days: kwargs['min_stay_days'] = int(new_min_stay_days)
                new_applicable_room_types = get_multiple_numerical_choices(ROOM_TYPES, f"Wprowadź nowe typy pokoi (obecne: {', '.join(discount.applicable_room_types) if discount.applicable_room_types else 'Brak'}, oddzielone przecinkami, pozostaw puste, aby zachować):", allow_empty=True)
                if new_applicable_room_types is not None: kwargs['applicable_room_types'] = new_applicable_room_types
                new_applicable_guest_ids_str = input(f"Wprowadź nowe ID gości (obecne: {', '.join(map(str, discount.applicable_guest_ids))}, oddzielone przecinkami, pozostaw puste, aby zachować): ")
                if new_applicable_guest_ids_str: kwargs['applicable_guest_ids'] = [g.strip() for g in new_applicable_guest_ids_str.split(',') if g.strip()]
                new_is_active = input(f"Czy rabat jest aktywny? (obecny: {discount.is_active}, tak/nie, pozostaw puste, aby zachować): ")
                if new_is_active: kwargs['is_active'] = new_is_active.lower() == 'tak'
                new_description = input(f"Wprowadź nowy opis (obecny: {discount.description}, pozostaw puste, aby zachować): ")
                if new_description: kwargs['description'] = new_description
                new_applicable_loyalty_tiers = get_multiple_numerical_choices(GUEST_LOYALTY_TIERS, f"Wprowadź nowe poziomy lojalności (obecne: {', '.join(map(str, discount.applicable_loyalty_tiers)) if discount.applicable_loyalty_tiers else 'Brak'}, oddzielone przecinkami, opcjonalnie): ", allow_empty=True)
                if new_applicable_loyalty_tiers is not None: kwargs['applicable_loyalty_tiers'] = new_applicable_loyalty_tiers

                if kwargs: discount_service.update_discount(discount_code, **kwargs)
                else: print(Fore.YELLOW + "Nie określono żadnych zmian.")
            else:
                print(Fore.RED + f"Rabat {discount_code} nie znaleziono.")

        elif choice == '4':
            print(Fore.CYAN + "\n--- Usuń Rabat ---")
            discount_code = input("Wprowadź kod rabatowy do usunięcia: ")
            discount_service.delete_discount(discount_code)

        # elif choice == '5':
        #     print(Fore.CYAN + "\n--- Znajdź Obowiązujące Rabaty ---")
        #     check_date_str = input("Wprowadź datę sprawdzania (RRRR-MM-DD, pozostaw puste dla dzisiaj): ")
        #     room_type = get_numerical_choice(ROOM_TYPES, "Wybierz typ pokoju (opcjonalnie):", allow_empty=True)
        #     guest_id = input("Wprowadź ID gościa (opcjonalnie): ")
        #     stay_duration_days_str = input("Wprowadź liczbę dni pobytu (0 jeśli brak wymogu): ")
        #     guest_loyalty_tier = get_numerical_choice(GUEST_LOYALTY_TIERS, "Wprowadź poziom lojalności gościa (pozostaw puste, aby pominąć):", allow_empty=True)

        #     stay_duration_days = int(stay_duration_days_str) if stay_duration_days_str else 0

        #     applicable_discounts = discount_service.find_applicable_discounts(
        #         check_date_str if check_date_str else None,
        #         room_type,
        #         guest_id if guest_id else None,
        #         stay_duration_days,
        #         guest_loyalty_tier
        #     )
        #     display_table(applicable_discounts, {"ID Rabatu": "discount_id", "Kod": "code", "Procent": "percentage", "Kwota Stała": "fixed_amount", "Ważny od": "valid_from", "Ważny do": "valid_to", "Min. Pobyt": "min_stay_days", "Typy Pokoi": "applicable_room_types", "ID Gości": "applicable_guest_ids", "Status": "is_active", "Poziomy Lojalności": "applicable_loyalty_tiers", "Opis": "description"}, "Obowiązujące Rabaty")

        elif choice == '5':
            break
        else:
            print(Fore.RED + "Nieprawidłowy wybór. Spróbuj ponownie.")

def get_numerical_choice(options, prompt, allow_empty=False):
    if isinstance(options, dict):
        options_list = list(options.keys())
    else:
        options_list = options

    while True:
        print(Fore.YELLOW + "\nDostępne opcje:")
        for i, option in enumerate(options_list, 1):
            print(Fore.YELLOW + f"{i}. {option}")
        if allow_empty:
            print(Fore.YELLOW + f"{len(options_list) + 1}. Pomiń / Brak wyboru")
        
        choice = input(Fore.GREEN + prompt)
        if allow_empty and not choice:
            return None
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(options_list):
                return options_list[choice_num - 1]
            else:
                print(Fore.RED + f"Wybierz liczbę od 1 do {len(options_list)}.")
        except ValueError:
            print(Fore.RED + "Wprowadź poprawną liczbę.")

def get_multiple_numerical_choices(options: list, prompt: str, allow_empty: bool = False):
    while True:
        print(Fore.YELLOW + prompt)
        for i, option in enumerate(options):
            print(f"{i + 1}. {option}")
        if allow_empty:
            print(f"{len(options) + 1}. Pomiń / Brak wyboru")
        print(Fore.CYAN + "Wprowadź numery oddzielone przecinkami (np. 1,3,5): ")
        choice_str = input(Fore.GREEN + "Wprowadź swój wybór: ")

        if allow_empty and choice_str == str(len(options) + 1):
            return None
        
        if not choice_str.strip(): 
            if allow_empty:
                return None
            else:
                print(Fore.RED + "Wybór jest wymagany. Spróbuj ponownie.")
                continue

        selected_options = []
        invalid_choice = False
        for c in choice_str.split(','):
            try:
                index = int(c.strip()) - 1
                if 0 <= index < len(options):
                    selected_options.append(options[index])
                else:
                    print(Fore.RED + f"Nieprawidłowy numer: {c.strip()}. Spróbuj ponownie.")
                    invalid_choice = True
                    break
            except ValueError:
                print(Fore.RED + f"Nieprawidłowy wybór: {c.strip()}. Wprowadź numery.")
                invalid_choice = True
                break
        
        if not invalid_choice:
            return selected_options

def main():
    parser = argparse.ArgumentParser(description="System Rezerwacji i Zarządzania Hotelami.")
    parser.add_argument("--config_path", type=str, default="config.json",
                        help="Ścieżka do pliku konfiguracyjnego (domyślnie: config.json).")
    args = parser.parse_args()

    config = {}
    try:
        with open(args.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(Fore.RED + f"Błąd: Plik konfiguracyjny '{args.config_path}' nie znaleziono. Upewnij się, że istnieje w katalogu głównym projektu lub podaj poprawną ścieżkę.")
        return
    except json.JSONDecodeError:
        print(Fore.RED + f"Błąd: Nieprawidłowy format pliku '{args.config_path}'. Upewnij się, że jest to poprawny JSON.")
        return

    data_directory = config.get("data_directory", "src/data") 
    
    data_manager = DataManager(data_dir=data_directory)
    db_manager = DatabaseManager()
    room_service = RoomService(db_manager)
    guest_service = GuestService(db_manager)
    housekeeping_service = HousekeepingService(db_manager, room_service)
    discount_service = DiscountService(db_manager)
    reservation_service = ReservationService(db_manager, room_service, guest_service, housekeeping_service, discount_service)
    payment_service = PaymentService(db_manager, reservation_service)
    report_service = ReportService(reservation_service, room_service, guest_service, payment_service, housekeeping_service)
    user_service = UserService(db_manager)

    current_user = None
    while current_user is None:
        print(Fore.CYAN + Style.BRIGHT + "\n--- Logowanie do Systemu --- ")
        username = input(Fore.GREEN + "Nazwa użytkownika: ")
        password = input(Fore.GREEN + "Hasło: ")
        current_user = user_service.authenticate_user(username, password)
        if current_user is None:
            print(Fore.RED + "Błąd logowania. Spróbuj ponownie.")

    while True:
        display_menu(current_user.role)
        choice = input(Fore.GREEN + "Wprowadź swój wybór: ")

        if current_user.role == "administrator":
            if choice == '1':
                manage_rooms_menu(room_service, current_user)
            elif choice == '2':
                manage_guests_menu(guest_service, current_user)
            elif choice == '3':
                manage_reservations_menu(reservation_service, room_service, guest_service, payment_service, current_user)
            elif choice == '4':
                manage_payments_menu(payment_service, current_user)
            elif choice == '5':
                manage_housekeeping_menu(housekeeping_service, room_service, current_user)
            elif choice == '6':
                manage_discounts_menu(discount_service, current_user)
            elif choice == '7':
                manage_users_menu(user_service, current_user)
            elif choice == '8':
                manage_reports_menu(report_service, room_service, reservation_service, current_user)
            elif choice == '9':
                print(Fore.CYAN + "Wyjście z systemu zarządzania hotelem. Do widzenia!")
                break
            else:
                print(Fore.RED + "Nieprawidłowy wybór. Spróbuj ponownie.")
        elif current_user.role == "recepcjonista":
            if choice == '1':
                manage_rooms_menu(room_service, current_user)
            elif choice == '2':
                manage_guests_menu(guest_service, current_user)
            elif choice == '3':
                manage_reservations_menu(reservation_service, room_service, guest_service, payment_service, current_user)
            elif choice == '4':
                manage_payments_menu(payment_service, current_user)
            elif choice == '5':
                manage_housekeeping_menu(housekeeping_service, room_service, current_user)
            elif choice == '6':
                manage_discounts_menu(discount_service, current_user)
            elif choice == '7':
                manage_reports_menu(report_service, room_service, reservation_service, current_user)
            elif choice == '8':
                print(Fore.CYAN + "Wyjście z systemu zarządzania hotelem. Do widzenia!")
                break
            else:
                print(Fore.RED + "Nieprawidłowy wybór. Spróbuj ponownie.")
        elif current_user.role == "pokojówka":
            if choice == '1':
                manage_housekeeping_menu(housekeeping_service, room_service, current_user)
            elif choice == '2':
                print(Fore.CYAN + "Wyjście z systemu zarządzania hotelem. Do widzenia!")
                break
            else:
                print(Fore.RED + "Nieprawidłowy wybór. Spróbuj ponownie.")
        else:
            print(Fore.RED + "Nieznana rola użytkownika.")

if __name__ == "__main__":
    main() 
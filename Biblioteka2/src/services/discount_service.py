import logging
from datetime import datetime

logger = logging.getLogger('hotel_reservation_app') 

class DiscountService:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        logger.info("DiscountService zainicjowany (DB).")

    def add_discount(self, code, percentage=0.0, fixed_amount=0.0,
                     valid_from_str=None, valid_to_str=None, min_stay_days=0,
                     applicable_room_types=None, applicable_guest_ids=None,
                     description="", applicable_loyalty_tiers=None):
        # Sprawdź czy kod już istnieje
        for d in self.db_manager.get_all_discounts():
            if d.code == code:
                print(f"Błąd: Rabat o kodzie '{code}' już istnieje.")
                logger.warning(f"Próba dodania istniejącego rabatu: {code}")
                return None
        if percentage <= 0 and fixed_amount <= 0:
            print("Błąd: Rabat musi mieć wartość procentową lub stałą kwotę.")
            logger.warning("Próba dodania rabatu bez wartości procentowej lub stałej kwoty.")
            return None
        all_discounts = self.db_manager.get_all_discounts()
        discount_id = f"DISC{len(all_discounts) + 1:04d}"
        valid_from = datetime.strptime(valid_from_str, "%Y-%m-%d") if valid_from_str else None
        valid_to = datetime.strptime(valid_to_str, "%Y-%m-%d") if valid_to_str else None
        discount_data = {
            "discount_id": discount_id,
            "code": code,
            "percentage": percentage,
            "fixed_amount": fixed_amount,
            "valid_from": valid_from,
            "valid_to": valid_to,
            "min_stay_days": min_stay_days,
            "applicable_room_types": applicable_room_types or [],
            "applicable_guest_ids": applicable_guest_ids or [],
            "is_active": True,
            "description": description,
            "applicable_loyalty_tiers": applicable_loyalty_tiers or []
        }
        discount = self.db_manager.add_discount(discount_data)
        print(f"Rabat '{code}' ({discount_id}) został dodany pomyślnie.")
        logger.info(f"Dodano rabat: {discount_id} ({code}).")
        return discount

    def get_discount(self, discount_code):
        for d in self.db_manager.get_all_discounts():
            if d.code == discount_code or d.discount_id == discount_code:
                logger.debug(f"Pobrano rabat: {discount_code}")
                return d
        logger.debug(f"Nie znaleziono rabatu: {discount_code}")
        return None

    def update_discount(self, discount_code, **kwargs):
        discount = self.get_discount(discount_code)
        if discount:
            update_data = {}
            for key, value in kwargs.items():
                if key in ['percentage', 'fixed_amount']:
                    try:
                        update_data[key] = float(value)#zamiana na float
                        logger.debug(f"Zaktualizowano {key} rabatu {discount.discount_id} na {value}.")
                    except ValueError as e:
                        print(f"Ostrzeżenie: Nieprawidłowa wartość dla {key}: {value}. Nie zaktualizowano. Szczegóły: {e}")
                        logger.warning(f"Nieprawidłowa wartość dla {key} rabatu {discount.discount_id}: {value} - {e}")
                elif key in ['valid_from', 'valid_to', 'valid_from_str', 'valid_to_str']:
                    if value:#zamiana daty 
                        try:
                            update_data[key.replace('_str','')] = datetime.strptime(value, "%Y-%m-%d")
                            logger.debug(f"Zaktualizowano {key} rabatu {discount.discount_id} na {value}.")
                        except ValueError as e:
                            print(f"Ostrzeżenie: Nieprawidłowy format daty dla {key}: {value}. Nie zaktualizowano. Szczegóły: {e}")
                            logger.warning(f"Nieprawidłowy format daty dla {key} rabatu {discount.discount_id}: {value} - {e}")
                    else:
                        update_data[key.replace('_str','')] = None
                        logger.debug(f"Wyczyszczono {key} rabatu {discount.discount_id}.")
                elif key in ['min_stay_days']:
                    try:
                        update_data[key] = int(value)
                        logger.debug(f"Zaktualizowano {key} rabatu {discount.discount_id} na {value}.")
                    except ValueError as e:
                        print(f"Ostrzeżenie: Nieprawidłowa wartość dla {key}: {value}. Nie zaktualizowano. Szczegóły: {e}")
                        logger.warning(f"Nieprawidłowa wartość dla {key} rabatu {discount.discount_id}: {value} - {e}")
                elif key in ['applicable_room_types', 'applicable_guest_ids', 'applicable_loyalty_tiers']:
                    update_data[key] = value if isinstance(value, list) else [item.strip() for item in value.split(',') if item.strip()]
                    logger.debug(f"Zaktualizowano {key} rabatu {discount.discount_id} na {value}.")
                elif key == 'is_active':
                    update_data[key] = bool(value)
                    logger.debug(f"Zaktualizowano {key} rabatu {discount.discount_id} na {value}.")
                else:
                    update_data[key] = value
                    logger.debug(f"Zaktualizowano {key} rabatu {discount.discount_id} na {value}.")
            self.db_manager.update_discount(discount.discount_id, update_data)
            print(f"Rabat '{discount.code}' został zaktualizowany pomyślnie.")
            logger.info(f"Zaktualizowano rabat: {discount.discount_id} ({discount.code}) z danymi: {kwargs}")
            return self.get_discount(discount.discount_id)
        print(f"Błąd: Rabat '{discount_code}' nie znaleziono.")
        logger.warning(f"Próba aktualizacji nieistniejącego rabatu: {discount_code}")
        return None

    def delete_discount(self, discount_code):
        discount = self.get_discount(discount_code)
        if discount:
            self.db_manager.delete_discount(discount.discount_id)
            print(f"Rabat '{discount_code}' został usunięty pomyślnie.")
            logger.info(f"Usunięto rabat: {discount_code}")
            return True
        print(f"Błąd: Rabat '{discount_code}' nie znaleziono.")
        logger.warning(f"Próba usunięcia nieistniejącego rabatu: {discount_code}")
        return False

    def list_all_discounts(self):
        discounts = self.db_manager.get_all_discounts()
        if not discounts:
            print("Brak rabatów w systemie.")
            logger.info("Brak rabatów w systemie do wyświetlenia.")
            return []
        logger.info("Wyświetlono wszystkie rabaty.")
        return discounts

    def find_applicable_discounts(self, check_date_str=None, room_type=None, guest_id=None, stay_duration_days=0, guest_loyalty_tier=None):
        applicable = []
        for d in self.db_manager.get_all_discounts():#pobieram rabaty
            valid = True
            if not d.is_active:
                valid = False
            if check_date_str:
                try:
                    check_date = datetime.strptime(check_date_str, "%Y-%m-%d").date()
                except ValueError:
                    valid = False
            else:
                check_date = datetime.now().date()
            if d.valid_from and check_date < d.valid_from.date():
                valid = False
            if d.valid_to and check_date > d.valid_to.date():
                valid = False
            if d.min_stay_days > 0 and stay_duration_days < d.min_stay_days:
                valid = False
            room_types = d.applicable_room_types if d.applicable_room_types is not None else []
            guest_ids = d.applicable_guest_ids if d.applicable_guest_ids is not None else []
            loyalty_tiers = d.applicable_loyalty_tiers if d.applicable_loyalty_tiers is not None else []
            if room_types and room_type not in room_types:
                valid = False
            if guest_ids and guest_id not in guest_ids:
                valid = False
            if loyalty_tiers and guest_loyalty_tier not in loyalty_tiers:
                valid = False
            if valid:
                applicable.append(d)
        if not applicable:
            print("Brak rabatów spełniających podane kryteria.")
            logger.info(f"Brak rabatów spełniających kryteria (data: {check_date_str}, typ pokoju: {room_type}, gość: {guest_id}, dni pobytu: {stay_duration_days}, poziom lojalności: {guest_loyalty_tier}).")
        else:
            logger.info(f"Znaleziono {len(applicable)} rabatów spełniających kryteria.")
        return applicable
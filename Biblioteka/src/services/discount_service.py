import logging
from src.models.discount import Discount
from src.data.data_manager import DataManager
from datetime import datetime

logger = logging.getLogger('hotel_reservation_app') 

class DiscountService:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.discounts = self.data_manager.load_discounts()
        logger.info("DiscountService zainicjowany.")

    def _save_discounts(self):
        self.data_manager.save_discounts(self.discounts)
        logger.debug("Zapisano rabaty do pliku.")

    def add_discount(self, code, percentage=0.0, fixed_amount=0.0,
                     valid_from_str=None, valid_to_str=None, min_stay_days=0,
                     applicable_room_types=None, applicable_guest_ids=None,
                     description="", applicable_loyalty_tiers=None):
        if any(d.code == code for d in self.discounts):
            print(f"Błąd: Rabat o kodzie '{code}' już istnieje.")
            logger.warning(f"Próba dodania istniejącego rabatu: {code}")
            return None
        
        if percentage <= 0 and fixed_amount <= 0:
            print("Błąd: Rabat musi mieć wartość procentową lub stałą kwotę.")
            logger.warning("Próba dodania rabatu bez wartości procentowej lub stałej kwoty.")
            return None

        discount_id = f"DISC{len(self.discounts) + 1:04d}"
        discount = Discount(discount_id, code, percentage, fixed_amount,
                            valid_from_str, valid_to_str, min_stay_days,
                            applicable_room_types, applicable_guest_ids, description=description, applicable_loyalty_tiers=applicable_loyalty_tiers)
        self.discounts.append(discount)
        self._save_discounts()
        print(f"Rabat '{code}' ({discount.discount_id}) został dodany pomyślnie.")
        logger.info(f"Dodano rabat: {discount_id} ({code}).")
        return discount

    def get_discount(self, discount_code):
        discount = next((d for d in self.discounts if d.code == discount_code or d.discount_id == discount_code), None)
        if discount:
            logger.debug(f"Pobrano rabat: {discount_code}")
        else:
            logger.debug(f"Nie znaleziono rabatu: {discount_code}")
        return discount

    def update_discount(self, discount_code, **kwargs):
        discount = self.get_discount(discount_code)
        if discount:
            for key, value in kwargs.items():
                if key in ['percentage', 'fixed_amount']:
                    try:
                        setattr(discount, key, float(value))
                        logger.debug(f"Zaktualizowano {key} rabatu {discount.discount_id} na {value}.")
                    except ValueError as e:
                        print(f"Ostrzeżenie: Nieprawidłowa wartość dla {key}: {value}. Nie zaktualizowano. Szczegóły: {e}")
                        logger.warning(f"Nieprawidłowa wartość dla {key} rabatu {discount.discount_id}: {value} - {e}")
                elif key in ['valid_from_str', 'valid_to_str']:
                    if value:
                        try:
                            datetime.strptime(value, "%Y-%m-%d")
                            setattr(discount, key, value)
                            logger.debug(f"Zaktualizowano {key} rabatu {discount.discount_id} na {value}.")
                        except ValueError as e:
                            print(f"Ostrzeżenie: Nieprawidłowy format daty dla {key}: {value}. Nie zaktualizowano. Szczegóły: {e}")
                            logger.warning(f"Nieprawidłowy format daty dla {key} rabatu {discount.discount_id}: {value} - {e}")
                    else:
                        setattr(discount, key, None)
                        logger.debug(f"Wyczyszczono {key} rabatu {discount.discount_id}.")
                elif key in ['min_stay_days']:
                    try:
                        setattr(discount, key, int(value))
                        logger.debug(f"Zaktualizowano {key} rabatu {discount.discount_id} na {value}.")
                    except ValueError as e:
                        print(f"Ostrzeżenie: Nieprawidłowa wartość dla {key}: {value}. Nie zaktualizowano. Szczegóły: {e}")
                        logger.warning(f"Nieprawidłowa wartość dla {key} rabatu {discount.discount_id}: {value} - {e}")
                elif key in ['applicable_room_types', 'applicable_guest_ids', 'applicable_loyalty_tiers']:
                    setattr(discount, key, [item.strip() for item in value.split(',') if item.strip()])
                    logger.debug(f"Zaktualizowano {key} rabatu {discount.discount_id} na {value}.")
                elif key == 'is_active':
                    setattr(discount, key, bool(value))
                    logger.debug(f"Zaktualizowano {key} rabatu {discount.discount_id} na {value}.")
                else:
                    setattr(discount, key, value)
                    logger.debug(f"Zaktualizowano {key} rabatu {discount.discount_id} na {value}.")
            self._save_discounts()
            print(f"Rabat '{discount.code}' został zaktualizowany pomyślnie.")
            logger.info(f"Zaktualizowano rabat: {discount.discount_id} ({discount.code}) z danymi: {kwargs}")
            return discount
        print(f"Błąd: Rabat '{discount_code}' nie znaleziono.")
        logger.warning(f"Próba aktualizacji nieistniejącego rabatu: {discount_code}")
        return None

    def delete_discount(self, discount_code):
        original_len = len(self.discounts)
        self.discounts = [d for d in self.discounts if d.code != discount_code and d.discount_id != discount_code]
        if len(self.discounts) < original_len:
            self._save_discounts()
            print(f"Rabat '{discount_code}' został usunięty pomyślnie.")
            logger.info(f"Usunięto rabat: {discount_code}")
            return True
        print(f"Błąd: Rabat '{discount_code}' nie znaleziono.")
        logger.warning(f"Próba usunięcia nieistniejącego rabatu: {discount_code}")
        return False

    def list_all_discounts(self):
        if not self.discounts:
            print("Brak rabatów w systemie.")
            logger.info("Brak rabatów w systemie do wyświetlenia.")
            return []
        logger.info("Wyświetlono wszystkie rabaty.")
        return self.discounts

    def find_applicable_discounts(self, check_date_str=None, room_type=None, guest_id=None, stay_duration_days=0, guest_loyalty_tier=None):
        applicable = [
            d for d in self.discounts 
            if d.is_valid(check_date_str, room_type, guest_id, stay_duration_days, guest_loyalty_tier)
        ]
        if not applicable:
            print("Brak rabatów spełniających podane kryteria.")
            logger.info(f"Brak rabatów spełniających kryteria (data: {check_date_str}, typ pokoju: {room_type}, gość: {guest_id}, dni pobytu: {stay_duration_days}, poziom lojalności: {guest_loyalty_tier}).")
        else:
            logger.info(f"Znaleziono {len(applicable)} rabatów spełniających kryteria.")
        return applicable


if __name__ == "__main__":
    dm = DataManager()
    discount_service = DiscountService(dm)

    print("\n--- Testowanie Usługi Rabatów ---")
    discount_service.add_discount("WIOSNA20", percentage=20.0, valid_from_str="2023-03-01", valid_to_str="2023-05-31", description="20% na wiosenne rezerwacje")
    discount_service.add_discount("LETNI100", fixed_amount=100.0, applicable_room_types=["apartament"], valid_from_str="2023-06-01", valid_to_str="2023-08-31", description="100 PLN zniżki na apartamenty w lecie")
    discount_service.add_discount("VIP5", percentage=5.0, applicable_guest_ids=["G001", "G003"], description="5% dla wybranych VIPów")
    discount_service.add_discount("DLUGI_POBYT", percentage=15.0, min_stay_days=5, description="15% na pobyty min. 5 dni")
    discount_service.add_discount("GOLDTIER", percentage=10.0, applicable_loyalty_tiers=["Gold", "Platinum"], description="10% dla klientów Gold i Platinum")

    print("\nWszystkie rabaty:")
    discount_service.list_all_discounts()

    print("\nTestowanie aktualizacji rabatu:")
    discount_service.update_discount("WIOSNA20", percentage=25.0, description="25% na wiosenne rezerwacje")
    print(discount_service.get_discount("WIOSNA20"))
    discount_service.update_discount("GOLDTIER", applicable_loyalty_tiers="Gold,Platinum,Silver")
    print(discount_service.get_discount("GOLDTIER"))

    print("\nTestowanie wyszukiwania rabatów:")
    print("Rabat na dzisiaj (2023-04-15) dla apartamentu, G001, 6 dni, Gold Tier:")
    applicable = discount_service.find_applicable_discounts(check_date_str="2023-04-15", room_type="apartament", guest_id="G001", stay_duration_days=6, guest_loyalty_tier="Gold")
    for d in applicable: print(d)

    print("Rabat na dzisiaj (2023-04-15) dla Gold Tier (Silver guest should not get it):")
    applicable_silver = discount_service.find_applicable_discounts(check_date_str="2023-04-15", guest_loyalty_tier="Silver")
    for d in applicable_silver: print(d)

    print("\nTestowanie usuwania rabatu:")
    discount_service.delete_discount("VIP5")
    discount_service.list_all_discounts()

    print("\nTestowanie nieaktywnego rabatu:")
    discount_service.update_discount("WIOSNA20", is_active=False)
    print(discount_service.get_discount("WIOSNA20"))
    print("Rabat WIOSNA20 ważny po dezaktywacji:", discount_service.get_discount("WIOSNA20").is_valid()) 
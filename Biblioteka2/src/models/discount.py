import json
from datetime import datetime

class Discount:
    def __init__(self, discount_id, code, percentage=0.0, fixed_amount=0.0,
                 valid_from_str=None, valid_to_str=None, min_stay_days=0,
                 applicable_room_types=None, applicable_guest_ids=None,
                 is_active=True, description="", applicable_loyalty_tiers=None):
        self.discount_id = discount_id
        self.code = code
        self.percentage = percentage
        self.fixed_amount = fixed_amount
        self.valid_from = valid_from_str
        self.valid_to = valid_to_str
        self.min_stay_days = min_stay_days
        self.applicable_room_types = applicable_room_types if applicable_room_types is not None else []
        self.applicable_guest_ids = applicable_guest_ids if applicable_guest_ids is not None else []
        self.is_active = is_active
        self.description = description
        self.applicable_loyalty_tiers = applicable_loyalty_tiers if applicable_loyalty_tiers is not None else []

    def to_dict(self):
        return {
            "discount_id": self.discount_id,
            "code": self.code,
            "percentage": self.percentage,
            "fixed_amount": self.fixed_amount,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "min_stay_days": self.min_stay_days,
            "applicable_room_types": self.applicable_room_types,
            "applicable_guest_ids": self.applicable_guest_ids,
            "is_active": self.is_active,
            "description": self.description,
            "applicable_loyalty_tiers": self.applicable_loyalty_tiers
        }

    @staticmethod
    def from_dict(data):
        return Discount(
            data["discount_id"],
            data["code"],
            data.get("percentage", 0.0),
            data.get("fixed_amount", 0.0),
            data.get("valid_from"),
            data.get("valid_to"),
            data.get("min_stay_days", 0),
            data.get("applicable_room_types"),
            data.get("applicable_guest_ids"),
            data.get("is_active", True),
            data.get("description", ""),
            data.get("applicable_loyalty_tiers")
        )

    def is_valid(self, check_date_str=None, room_type=None, guest_id=None, stay_duration_days=0, guest_loyalty_tier=None):
        if not self.is_active:
            return False

        current_date = datetime.now().date()
        if check_date_str:
            try:
                check_date = datetime.strptime(check_date_str, "%Y-%m-%d").date()
            except ValueError:
                return False 
        else:
            check_date = current_date

        if self.valid_from:
            valid_from_date = datetime.strptime(self.valid_from, "%Y-%m-%d").date()
            if check_date < valid_from_date:
                return False
        if self.valid_to:
            valid_to_date = datetime.strptime(self.valid_to, "%Y-%m-%d").date()
            if check_date > valid_to_date:
                return False

        if self.min_stay_days > 0 and stay_duration_days < self.min_stay_days:
            return False

        if self.applicable_room_types and room_type not in self.applicable_room_types:
            return False

        if self.applicable_guest_ids and guest_id not in self.applicable_guest_ids:
            return False

        if self.applicable_loyalty_tiers and guest_loyalty_tier not in self.applicable_loyalty_tiers:
            return False

        return True

    def calculate_discount_amount(self, original_price):
        if self.percentage > 0:
            return original_price * (self.percentage / 100)
        elif self.fixed_amount > 0:
            return self.fixed_amount
        return 0

    def __str__(self):
        status = "Aktywny" if self.is_active else "Nieaktywny"
        validity = f"Od: {self.valid_from if self.valid_from else 'Brak'} Do: {self.valid_to if self.valid_to else 'Brak'}"
        room_types = f"Typy pokoi: {', '.join(self.applicable_room_types)}" if self.applicable_room_types else "Wszystkie"
        guest_ids = f"ID Gości: {', '.join(self.applicable_guest_ids)}" if self.applicable_guest_ids else "Wszyscy"
        min_stay = f"Min. pobyt: {self.min_stay_days} dni" if self.min_stay_days > 0 else "Brak wymogu"
        loyalty_tiers = f"Poziomy lojalności: {', '.join(self.applicable_loyalty_tiers)}" if self.applicable_loyalty_tiers else "Wszystkie"

        discount_type = ""
        if self.percentage > 0: discount_type = f"{self.percentage:.2f}%"
        elif self.fixed_amount > 0: discount_type = f"{self.fixed_amount:.2f} PLN stała kwota"

        return (f"Rabat ID: {self.discount_id} | Kod: {self.code} | Wartość: {discount_type} | "
                f"Status: {status} | Ważność: {validity} | {room_types} | {guest_ids} | {min_stay} | {loyalty_tiers} | Opis: {self.description}")



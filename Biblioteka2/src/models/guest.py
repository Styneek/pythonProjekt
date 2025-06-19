import json
from src.models.base_model import BaseModel

class Guest(BaseModel):
    def __init__(self, guest_id, first_name, last_name, id_document, contact_info, is_vip=False, is_loyal_customer=False, preferences=None, stay_history=None, loyalty_tier="Bronze"):
        self.guest_id = guest_id
        self.first_name = first_name
        self.last_name = last_name
        self.id_document = id_document
        self.contact_info = contact_info  
        self.is_vip = is_vip
        self.is_loyal_customer = is_loyal_customer
        self.preferences = preferences if preferences is not None else []
        self.stay_history = stay_history if stay_history is not None else []
        self.loyalty_tier = loyalty_tier 

    def to_dict(self):
        return {
            "guest_id": self.guest_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "id_document": self.id_document,
            "contact_info": self.contact_info,
            "is_vip": self.is_vip,
            "is_loyal_customer": self.is_loyal_customer,
            "preferences": self.preferences,
            "stay_history": self.stay_history,
            "loyalty_tier": self.loyalty_tier
        }

    @staticmethod
    def from_dict(data):
        return Guest(
            data.get("guest_id"),
            data.get("first_name", ""),
            data.get("last_name", ""),
            data.get("id_document", ""),
            data.get("contact_info", {}),
            data.get("is_vip", False),
            data.get("is_loyal_customer", False),
            data.get("preferences", []),
            data.get("stay_history", []),
            data.get("loyalty_tier", "Bronze")
        )

    def add_stay_record(self, stay_details):
        self.stay_history.append(stay_details)

    def __str__(self):
        return f"ID Gościa: {self.guest_id}, Imię i Nazwisko: {self.first_name} {self.last_name}, VIP: {'Tak' if self.is_vip else 'Nie'}, Stały Klient: {'Tak' if self.is_loyal_customer else 'Nie'}"

    @property
    def formatted_contact_info(self):
        contact_parts = []
        if "email" in self.contact_info and self.contact_info["email"]:
            contact_parts.append(f"email: {self.contact_info['email']}")
        if "phone" in self.contact_info and self.contact_info["phone"]:
            contact_parts.append(f"tel: {self.contact_info['phone']}")
        return ", ".join(contact_parts) if contact_parts else "N/A"


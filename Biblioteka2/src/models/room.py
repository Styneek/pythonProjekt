import json
from src.models.base_model import BaseModel

class Room(BaseModel):
    def __init__(self, number, floor, room_type, price, amenities=None, status="dostępny"):
        self.number = number
        self.floor = floor
        self.room_type = room_type
        self.price = price
        self.amenities = amenities if amenities is not None else []
        self.status = status 

    def to_dict(self):
        return {
            "number": self.number,
            "floor": self.floor,
            "room_type": self.room_type,
            "price": self.price,
            "amenities": self.amenities,
            "status": self.status
        }

    @staticmethod
    def from_dict(data):
        return Room(
            data["number"],
            data["floor"],
            data["room_type"],
            data["price"],
            data["amenities"],
            data["status"]
        )

    def update_status(self, new_status):
        valid_statuses = ["dostępny", "zajęty", "sprzątanie", "niedostępny"]
        if new_status in valid_statuses:
            self.status = new_status
            return True
        return False

    def __str__(self):
        return f"Pokój {self.number} (Typ: {self.room_type}, Cena: {self.price:.2f}, Status: {self.status})"
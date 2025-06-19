import json
from src.models.base_model import BaseModel
from src.constants.status_mappings import REVERSE_RESERVATION_STATUS_MAPPING

class Reservation(BaseModel):
    def __init__(self, reservation_id, guest_id, room_number, check_in_date, check_out_date, status="active", total_price=0.0, payment_status="pending", applied_discount_id=None):
        self.reservation_id = reservation_id
        self.guest_id = guest_id
        self.room_number = room_number
        self.check_in_date = check_in_date
        self.check_out_date = check_out_date
        self.status = status  
        self.total_price = total_price
        self.payment_status = payment_status 
        self.applied_discount_id = applied_discount_id

    def to_dict(self):
        return {
            "reservation_id": self.reservation_id,
            "guest_id": self.guest_id,
            "room_number": self.room_number,
            "check_in_date": self.check_in_date,
            "check_out_date": self.check_out_date,
            "status": self.status,
            "total_price": self.total_price,
            "payment_status": self.payment_status,
            "applied_discount_id": self.applied_discount_id
        }

    @staticmethod
    def from_dict(data):
        return Reservation(
            data["reservation_id"],
            data["guest_id"],
            data["room_number"],
            data["check_in_date"],
            data["check_out_date"],
            data["status"],
            data["total_price"],
            data["payment_status"],
            data.get("applied_discount_id")
        )

    def update_status(self, new_status):
        valid_statuses = ["active", "cancelled", "checked_in", "checked_out"]
        if new_status in valid_statuses:
            self.status = new_status
            return True
        return False

    def __str__(self):
        status_pl = REVERSE_RESERVATION_STATUS_MAPPING.get(self.status, self.status)
        return f"ID Rezerwacji: {self.reservation_id}, ID Gościa: {self.guest_id}, Pokój: {self.room_number}, Daty: {self.check_in_date} do {self.check_out_date}, Status: {status_pl}"
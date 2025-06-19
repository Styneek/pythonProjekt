import json
from datetime import datetime
from src.models.base_model import BaseModel

class Payment(BaseModel):
    def __init__(self, payment_id, reservation_id, amount, payment_date, payment_method, status="completed"):
        self.payment_id = payment_id
        self.reservation_id = reservation_id
        self.amount = amount
        self.payment_date = payment_date 
        self.payment_method = payment_method
        self.status = status 

    def to_dict(self):
        return {
            "payment_id": self.payment_id,
            "reservation_id": self.reservation_id,
            "amount": self.amount,
            "payment_date": self.payment_date,
            "payment_method": self.payment_method,
            "status": self.status
        }

    @staticmethod
    def from_dict(data):
        return Payment(
            data["payment_id"],
            data["reservation_id"],
            data["amount"],
            data["payment_date"],
            data["payment_method"],
            data["status"]
        )

    def __str__(self):
        return f"ID Płatności: {self.payment_id}, ID Rezerwacji: {self.reservation_id}, Kwota: {self.amount:.2f}, Data: {self.payment_date}, Metoda: {self.payment_method}, Status: {self.status}"


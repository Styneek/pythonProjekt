import json
from datetime import datetime
from src.models.base_model import BaseModel

class Invoice(BaseModel):
    def __init__(self, invoice_id, reservation_id, guest_id, issue_date, due_date, total_amount, paid_amount=0.0, status="pending", line_items=None):
        self.invoice_id = invoice_id
        self.reservation_id = reservation_id
        self.guest_id = guest_id
        self.issue_date = issue_date 
        self.due_date = due_date     
        self.total_amount = total_amount
        self.paid_amount = paid_amount
        self.status = status 
        self.line_items = line_items if line_items is not None else [] 

    def to_dict(self):
        return {
            "invoice_id": self.invoice_id,
            "reservation_id": self.reservation_id,
            "guest_id": self.guest_id,
            "issue_date": self.issue_date,
            "due_date": self.due_date,
            "total_amount": self.total_amount,
            "paid_amount": self.paid_amount,
            "status": self.status,
            "line_items": self.line_items
        }

    @staticmethod
    def from_dict(data):
        return Invoice(
            data["invoice_id"],
            data["reservation_id"],
            data["guest_id"],
            data["issue_date"],
            data["due_date"],
            data["total_amount"],
            data["paid_amount"],
            data["status"],
            data["line_items"]
        )

    def add_line_item(self, description, amount):
        self.line_items.append({'description': description, 'amount': amount})
        self.total_amount += amount

    def record_payment(self, amount):
        self.paid_amount += amount
        if self.paid_amount >= self.total_amount:
            self.status = "paid"
        elif self.paid_amount > 0 and self.paid_amount < self.total_amount:
            self.status = "partially_paid" 
        else:
            self.status = "pending"

    def __str__(self):
        return (f"Faktura ID: {self.invoice_id}, Rezerwacja ID: {self.reservation_id}, "
                f"ID Gościa: {self.guest_id}, Suma: {self.total_amount:.2f}, Zapłacono: {self.paid_amount:.2f}, "
                f"Status: {self.status}")


import json
import os
from src.models.room import Room
from src.models.guest import Guest
from src.models.reservation import Reservation
from src.models.payment import Payment
from src.models.invoice import Invoice
from src.models.housekeeping_task import HousekeepingTask
from src.models.user import User
from src.models.discount import Discount

class DataManager:
    def __init__(self, data_dir="src/data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.rooms_file = os.path.join(self.data_dir, "rooms.json")
        self.guests_file = os.path.join(self.data_dir, "guests.json")
        self.reservations_file = os.path.join(self.data_dir, "reservations.json")
        self.payments_file = os.path.join(self.data_dir, "payments.json")
        self.invoices_file = os.path.join(self.data_dir, "invoices.json")
        self.housekeeping_tasks_file = os.path.join(self.data_dir, "housekeeping_tasks.json")
        self.users_file = os.path.join(self.data_dir, "users.json")
        self.discounts_file = os.path.join(self.data_dir, "discounts.json")

    @classmethod
    def default_instance(cls):
        return cls(data_dir="src/data")

    def _load_data(self, file_path):
        if not os.path.exists(file_path):
            return []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def _save_data(self, data, file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def load_rooms(self):
        rooms_data = self._load_data(self.rooms_file)
        return [Room.from_dict(data) for data in rooms_data]

    def save_rooms(self, rooms):
        rooms_data = [room.to_dict() for room in rooms]
        self._save_data(rooms_data, self.rooms_file)

    def load_guests(self):
        guests_data = self._load_data(self.guests_file)
        return [Guest.from_dict(data) for data in guests_data]

    def save_guests(self, guests):
        guests_data = [guest.to_dict() for guest in guests]
        self._save_data(guests_data, self.guests_file)

    def load_reservations(self):
        reservations_data = self._load_data(self.reservations_file)
        return [Reservation.from_dict(data) for data in reservations_data]

    def save_reservations(self, reservations):
        reservations_data = [res.to_dict() for res in reservations]
        self._save_data(reservations_data, self.reservations_file)

    def load_payments(self):
        payments_data = self._load_data(self.payments_file)
        return [Payment.from_dict(data) for data in payments_data]

    def save_payments(self, payments):
        payments_data = [payment.to_dict() for payment in payments]
        self._save_data(payments_data, self.payments_file)

    def load_invoices(self):
        invoices_data = self._load_data(self.invoices_file)
        return [Invoice.from_dict(data) for data in invoices_data]

    def save_invoices(self, invoices):
        invoices_data = [invoice.to_dict() for invoice in invoices]
        self._save_data(invoices_data, self.invoices_file)

    def load_housekeeping_tasks(self):
        tasks_data = self._load_data(self.housekeeping_tasks_file)
        return [HousekeepingTask.from_dict(data) for data in tasks_data]

    def save_housekeeping_tasks(self, tasks):
        tasks_data = [task.to_dict() for task in tasks]
        self._save_data(tasks_data, self.housekeeping_tasks_file)

    def load_users(self):
        users_data = self._load_data(self.users_file)
        return [User.from_dict(data) for data in users_data]

    def save_users(self, users):
        users_data = [user.to_dict() for user in users]
        self._save_data(users_data, self.users_file)

    def load_discounts(self):
        discounts_data = self._load_data(self.discounts_file)
        return [Discount.from_dict(data) for data in discounts_data]

    def save_discounts(self, discounts):
        discounts_data = [discount.to_dict() for discount in discounts]
        self._save_data(discounts_data, self.discounts_file)


if __name__ == "__main__":
    dm = DataManager()

  
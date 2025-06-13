import json
import os
from datetime import datetime
from .db_manager import DatabaseManager
from .models import *
import logging

logger = logging.getLogger('hotel_reservation_app')

class DataMigrator:
    def __init__(self, data_dir="src/data"):
        self.data_dir = data_dir
        self.db_manager = DatabaseManager()

    def _load_json_data(self, filename):
        file_path = os.path.join(self.data_dir, filename)
        if not os.path.exists(file_path):
            return []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {filename}")
            return []

    def migrate_rooms(self):
        rooms_data = self._load_json_data("rooms.json")
        for room_data in rooms_data:
            self.db_manager.add_room(room_data)
        logger.info(f"Migrated {len(rooms_data)} rooms")

    def migrate_guests(self):
        guests_data = self._load_json_data("guests.json")
        for guest_data in guests_data:
            self.db_manager.add_guest(guest_data)
        logger.info(f"Migrated {len(guests_data)} guests")

    def migrate_reservations(self):
        reservations_data = self._load_json_data("reservations.json")
        for reservation_data in reservations_data:
            mapped_data = {
                'reservation_id': reservation_data.get('reservation_id'),
                'guest_id': reservation_data.get('guest_id'),
                'room_number': reservation_data.get('room_number'),
                'check_in': datetime.strptime(reservation_data.get('check_in_date', ''), '%Y-%m-%d') if reservation_data.get('check_in_date') else None,
                'check_out': datetime.strptime(reservation_data.get('check_out_date', ''), '%Y-%m-%d') if reservation_data.get('check_out_date') else None,
                'total_price': reservation_data.get('total_price'),
                'status': reservation_data.get('status', 'pending')
            }
            self.db_manager.add_reservation(mapped_data)
        logger.info(f"Migrated {len(reservations_data)} reservations")

    def migrate_payments(self):
        payments_data = self._load_json_data("payments.json")
        for payment_data in payments_data:
            mapped_data = {
                'payment_id': payment_data.get('payment_id'),
                'reservation_id': payment_data.get('reservation_id'),
                'amount': payment_data.get('amount'),
                'payment_date': datetime.strptime(payment_data.get('payment_date', ''), '%Y-%m-%d %H:%M:%S') if payment_data.get('payment_date') else None,
                'payment_method': payment_data.get('payment_method'),
                'status': payment_data.get('status', 'pending')
            }
            self.db_manager.add_payment(mapped_data)
        logger.info(f"Migrated {len(payments_data)} payments")

    def migrate_invoices(self):
        invoices_data = self._load_json_data("invoices.json")
        for invoice_data in invoices_data:
            mapped_data = {
                'invoice_id': invoice_data.get('invoice_id'),
                'reservation_id': invoice_data.get('reservation_id'),
                'guest_id': invoice_data.get('guest_id'),
                'issue_date': datetime.strptime(invoice_data.get('issue_date', ''), '%Y-%m-%d') if invoice_data.get('issue_date') else None,
                'due_date': datetime.strptime(invoice_data.get('due_date', ''), '%Y-%m-%d') if invoice_data.get('due_date') else None,
                'total_amount': invoice_data.get('total_amount'),
                'paid_amount': invoice_data.get('paid_amount', 0.0),
                'status': invoice_data.get('status', 'pending'),
                'line_items': invoice_data.get('line_items', [])
            }
            self.db_manager.add_invoice(mapped_data)
        logger.info(f"Migrated {len(invoices_data)} invoices")

    def migrate_housekeeping_tasks(self):
        tasks_data = self._load_json_data("housekeeping_tasks.json")
        for task_data in tasks_data:
            mapped_data = {
                'task_id': task_data.get('task_id'),
                'room_number': task_data.get('room_number'),
                'assigned_to': task_data.get('assigned_to'),
                'due_date': datetime.strptime(task_data.get('due_date', ''), '%Y-%m-%d') if task_data.get('due_date') else None,
                'status': task_data.get('status', 'pending'),
                'completed_date': datetime.strptime(task_data.get('completed_date', ''), '%Y-%m-%d %H:%M:%S') if task_data.get('completed_date') else None,
                'notes': task_data.get('notes', '')
            }
            self.db_manager.add_housekeeping_task(mapped_data)
        logger.info(f"Migrated {len(tasks_data)} housekeeping tasks")

    def migrate_users(self):
        users_data = self._load_json_data("users.json")
        for user_data in users_data:
            self.db_manager.add_user(user_data)
        logger.info(f"Migrated {len(users_data)} users")

    def migrate_discounts(self):
        discounts_data = self._load_json_data("discounts.json")
        for discount_data in discounts_data:
            mapped_data = {
                'discount_id': discount_data.get('discount_id'),
                'code': discount_data.get('code'),
                'percentage': discount_data.get('percentage', 0.0),
                'fixed_amount': discount_data.get('fixed_amount', 0.0),
                'valid_from': datetime.strptime(discount_data.get('valid_from', ''), '%Y-%m-%d') if discount_data.get('valid_from') else None,
                'valid_to': datetime.strptime(discount_data.get('valid_to', ''), '%Y-%m-%d') if discount_data.get('valid_to') else None,
                'min_stay_days': discount_data.get('min_stay_days', 0),
                'applicable_room_types': discount_data.get('applicable_room_types', []),
                'applicable_guest_ids': discount_data.get('applicable_guest_ids', []),
                'is_active': discount_data.get('is_active', True),
                'description': discount_data.get('description', ''),
                'applicable_loyalty_tiers': discount_data.get('applicable_loyalty_tiers', [])
            }
            self.db_manager.add_discount(mapped_data)
        logger.info(f"Migrated {len(discounts_data)} discounts")

    def migrate_all(self):
        logger.info("Starting data migration...")
        self.migrate_rooms()
        self.migrate_guests()
        self.migrate_reservations()
        self.migrate_payments()
        self.migrate_invoices()
        self.migrate_housekeeping_tasks()
        self.migrate_users()
        self.migrate_discounts()
        
        logger.info("Data migration completed successfully!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    migrator = DataMigrator()
    migrator.migrate_all() 
from sqlalchemy.orm import Session
from datetime import datetime
from .models import *
from .config import get_db
import logging

logger = logging.getLogger('hotel_reservation_app')

class DatabaseManager:
    def __init__(self):
        self.db = next(get_db()) #uruchamia generator do 1 yield, zwraca bd
        logger.info("baza została zainicjalizowana")

    def __del__(self):
        if hasattr(self, 'db'): #sprawdza czy obniekt ma atrybut 'db', tak = zamyka polaczenie z baza
            self.db.close()

#tworzenie zapytan --------------------------------------------

#pobieram wszyskie rekordy z tabeli Room
    def get_all_rooms(self):
        return self.db.query(Room).all()
    
#fitruje pobieram po numerze konkretny pokoj
    def get_room(self, room_number):
        return self.db.query(Room).filter(Room.number == room_number).first()

    def add_room(self, room_data):
        existing_room = self.get_room(room_data['number']) # czy istnieje
        if existing_room:
            for key, value in room_data.items():
                setattr(existing_room, key, value) #setattr dynamiczne ustawienie atrybutow w pyhonie
            self.db.commit() #i zapisuje
            return existing_room
        #tworze nowy obiekt klasy Room
        else:
            room = Room(**room_data) #rozpakowuje slownik do arg konstruktora klasy Room i dodaje
            self.db.add(room)
            self.db.commit()
            return room

    def update_room(self, room_number, room_data):
        room = self.get_room(room_number) #sprawdzam czy jest
        if room:
            for key, value in room_data.items(): #przechodze przez wszyskie k-v 
                setattr(room, key, value) #setattr dynamiczne ustawienie atrybutow w pyhonie
            self.db.commit()
        return room

    def get_all_guests(self):
        return self.db.query(Guest).all()

    def get_guest(self, guest_id):
        return self.db.query(Guest).filter(Guest.guest_id == guest_id).first()

    def add_guest(self, guest_data):
        existing_guest = self.get_guest(guest_data['guest_id'])
        if existing_guest:
            for key, value in guest_data.items():
                setattr(existing_guest, key, value)
            self.db.commit()
            return existing_guest
        else:
            guest = Guest(**guest_data)
            self.db.add(guest)
            self.db.commit()
            return guest

    def update_guest(self, guest_id, guest_data):
        guest = self.get_guest(guest_id)
        if guest:
            for key, value in guest_data.items():
                setattr(guest, key, value)
            self.db.commit()
        return guest

    def get_all_reservations(self):
        return self.db.query(Reservation).all()

    def get_reservation(self, reservation_id):
        return self.db.query(Reservation).filter(Reservation.reservation_id == reservation_id).first()

    def add_reservation(self, reservation_data):
        existing_reservation = self.get_reservation(reservation_data['reservation_id'])
        if existing_reservation:
            for key, value in reservation_data.items():
                setattr(existing_reservation, key, value)
            self.db.commit()
            return existing_reservation
        else:
            reservation = Reservation(**reservation_data)
            self.db.add(reservation)
            self.db.commit()
            return reservation

    def update_reservation(self, reservation_id, reservation_data):
        reservation = self.get_reservation(reservation_id)
        if reservation:
            for key, value in reservation_data.items():
                setattr(reservation, key, value)
            self.db.commit()
        return reservation

    def get_all_payments(self):
        return self.db.query(Payment).all()

    def get_payment(self, payment_id):
        return self.db.query(Payment).filter(Payment.payment_id == payment_id).first()

    def add_payment(self, payment_data):
        existing_payment = self.get_payment(payment_data['payment_id'])
        if existing_payment:
            for key, value in payment_data.items():
                setattr(existing_payment, key, value)
            self.db.commit()
            return existing_payment
        else:
            payment = Payment(**payment_data)
            self.db.add(payment)
            self.db.commit()
            return payment

    def get_all_invoices(self):
        return self.db.query(Invoice).all()

    def get_invoice(self, invoice_id):
        return self.db.query(Invoice).filter(Invoice.invoice_id == invoice_id).first()

    def add_invoice(self, invoice_data):
        existing_invoice = self.get_invoice(invoice_data['invoice_id'])
        if existing_invoice:
            for key, value in invoice_data.items():
                setattr(existing_invoice, key, value)
            self.db.commit()
            return existing_invoice
        else:
            invoice = Invoice(**invoice_data)
            self.db.add(invoice)
            self.db.commit()
            return invoice

    def update_invoice(self, invoice_id, invoice_data):
        invoice = self.get_invoice(invoice_id)
        if invoice:
            for key, value in invoice_data.items():
                setattr(invoice, key, value)
            self.db.commit()
        return invoice

    def get_all_housekeeping_tasks(self):
        return self.db.query(HousekeepingTask).all()

    def get_housekeeping_task(self, task_id):
        return self.db.query(HousekeepingTask).filter(HousekeepingTask.task_id == task_id).first()

    def add_housekeeping_task(self, task_data):
        existing_task = self.get_housekeeping_task(task_data['task_id'])
        if existing_task:
            for key, value in task_data.items():
                setattr(existing_task, key, value)
            self.db.commit()
            return existing_task
        else:
            task = HousekeepingTask(**task_data)
            self.db.add(task)
            self.db.commit()
            return task

    def update_housekeeping_task(self, task_id, task_data):
        task = self.get_housekeeping_task(task_id)
        if task:
            for key, value in task_data.items():
                setattr(task, key, value)
            self.db.commit()
        return task

    def delete_housekeeping_task(self, task_id):
        task = self.get_housekeeping_task(task_id)
        if task:
            self.db.delete(task)
            self.db.commit()
            return True
        return False

    def get_all_users(self):
        return self.db.query(User).all()

    def get_user(self, username):
        return self.db.query(User).filter(User.username == username).first()

    def add_user(self, user_data):
        existing_user = self.get_user(user_data['username'])
        if existing_user:
            for key, value in user_data.items():
                setattr(existing_user, key, value)
            self.db.commit()
            return existing_user
        else:
            user = User(**user_data)
            self.db.add(user)
            self.db.commit()
            return user

    def get_all_discounts(self):
        return self.db.query(Discount).all()

    def get_discount(self, discount_id):
        return self.db.query(Discount).filter(Discount.discount_id == discount_id).first()

    def add_discount(self, discount_data):
        existing_discount = self.get_discount(discount_data['discount_id'])
        if existing_discount:
            for key, value in discount_data.items():
                setattr(existing_discount, key, value)
            self.db.commit()
            return existing_discount
        else:
            discount = Discount(**discount_data)
            self.db.add(discount)
            self.db.commit()
            return discount

    def update_discount(self, discount_id, discount_data):
        discount = self.get_discount(discount_id)
        if discount:
            for key, value in discount_data.items():
                setattr(discount, key, value)
            self.db.commit()
        return discount

    def delete_discount(self, discount_id):
        discount = self.get_discount(discount_id)
        if discount:
            self.db.delete(discount)
            self.db.commit()
            return True
        return False

    def delete_user(self, username):
        user = self.get_user(username)
        if user:
            self.db.delete(user)
            self.db.commit()
            return True
        return False

    def update_user(self, username, user_data):
        user = self.get_user(username)
        if user:
            for key, value in user_data.items():
                setattr(user, key, value)
            self.db.commit()
        return user 
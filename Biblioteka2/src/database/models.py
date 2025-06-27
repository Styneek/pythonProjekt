from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, DateTime, JSON, Table, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base() # klasa Base od ktorej bede dziedziczyly wszyskie twoje metody, dzieki temu SQLAlchemy wie ze klasy maja byc zamieniane na tabele w bazie danych


#tworzenie tabel 
class Room(Base):
    __tablename__ = 'rooms'
    
    number = Column(String, primary_key=True)
    floor = Column(Integer, nullable=False)
    room_type = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    amenities = Column(JSON, nullable=False)
    status = Column(String, nullable=False)
    __table_args__ = (
        CheckConstraint("price >= 0", name="check_room_price_positive"),
        CheckConstraint("status IN ('available', 'occupied', 'maintenance', 'out_of_service')", name="check_room_status"),
    )

class Guest(Base):
    __tablename__ = 'guests'
    
    guest_id = Column(String, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    id_document = Column(String, nullable=False, unique=True)
    contact_info = Column(JSON, nullable=False)
    is_vip = Column(Boolean, default=False, nullable=False)
    is_loyal_customer = Column(Boolean, default=False, nullable=False)
    preferences = Column(JSON, default=[], nullable=False)
    loyalty_tier = Column(String, default="Bronze", nullable=False)
    stay_history = Column(JSON, default=[], nullable=False)
    __table_args__ = (
        CheckConstraint("loyalty_tier IN ('Bronze', 'Silver', 'Gold', 'Platinum')", name='check_loyalty_tier'),
    )

class Reservation(Base):
    __tablename__ = 'reservations'
    
    reservation_id = Column(String, primary_key=True)
    guest_id = Column(String, ForeignKey('guests.guest_id'), nullable=False)
    room_number = Column(String, ForeignKey('rooms.number'), nullable=False)
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    payment_status = Column(String, nullable=False)
    
    guest = relationship("Guest")
    room = relationship("Room")
    __table_args__ = (
        CheckConstraint("total_price >= 0", name="check_reservation_price_positive"),
        CheckConstraint("status IN ('pending', 'confirmed', 'cancelled', 'completed')", name="check_reservation_status"),
        CheckConstraint("payment_status IN ('pending', 'paid', 'failed', 'refunded')", name="check_payment_status"),
    )

class Payment(Base):
    __tablename__ = 'payments'
    
    payment_id = Column(String, primary_key=True)
    reservation_id = Column(String, ForeignKey('reservations.reservation_id'), nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, nullable=False)
    payment_method = Column(String, nullable=False)
    status = Column(String, nullable=False)
    
    reservation = relationship("Reservation")
    __table_args__ = (
        CheckConstraint("amount >= 0", name="check_payment_amount_positive"),
        CheckConstraint("status IN ('pending', 'completed', 'failed', 'refunded')", name="check_payment_status"),
    )

class Invoice(Base):
    __tablename__ = 'invoices'
    
    invoice_id = Column(String, primary_key=True)
    reservation_id = Column(String, ForeignKey('reservations.reservation_id'), nullable=False)
    guest_id = Column(String, ForeignKey('guests.guest_id'), nullable=False)
    issue_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    total_amount = Column(Float, nullable=False)
    paid_amount = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    line_items = Column(JSON, nullable=False)
    
    reservation = relationship("Reservation")
    guest = relationship("Guest")
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="check_invoice_total_amount_positive"),
        CheckConstraint("paid_amount >= 0", name="check_invoice_paid_amount_positive"),
        CheckConstraint("status IN ('pending', 'paid', 'overdue', 'cancelled')", name="check_invoice_status"),
    )

class HousekeepingTask(Base):
    __tablename__ = 'housekeeping_tasks'
    
    task_id = Column(String, primary_key=True)
    room_number = Column(String, ForeignKey('rooms.number'), nullable=False)
    assigned_to = Column(String, nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)
    completed_date = Column(DateTime, nullable=True)
    notes = Column(String, nullable=False)
    
    room = relationship("Room")
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'cancelled')", name="check_housekeeping_status"),
    )

class User(Base):
    __tablename__ = 'users'
    
    username = Column(String, primary_key=True)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    employee_id = Column(String, nullable=False, unique=True)
    __table_args__ = (
        CheckConstraint("role IN ('pokojówka', 'recepcjonista', 'administrator')", name="check_user_role"),
    )

    def has_permission(self, required_role):
        role_hierarchy = {
            "pokojówka": 1,
            "recepcjonista": 2,
            "administrator": 3
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)

class Discount(Base):
    __tablename__ = 'discounts'
    
    discount_id = Column(String, primary_key=True)
    code = Column(String, nullable=False, unique=True)
    percentage = Column(Float, nullable=False)
    fixed_amount = Column(Float, nullable=False)
    valid_from = Column(DateTime, nullable=True)
    valid_to = Column(DateTime, nullable=True)
    min_stay_days = Column(Integer, nullable=False)
    applicable_room_types = Column(JSON, nullable=False)
    applicable_guest_ids = Column(JSON, nullable=False)
    is_active = Column(Boolean, nullable=False)
    description = Column(String, nullable=False)
    applicable_loyalty_tiers = Column(JSON, nullable=False)
    __table_args__ = (
        CheckConstraint("percentage >= 0 AND percentage <= 100", name="check_discount_percentage"),
        CheckConstraint("fixed_amount >= 0", name="check_discount_fixed_amount"),
    ) 
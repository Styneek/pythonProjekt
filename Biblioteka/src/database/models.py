from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, DateTime, JSON, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Room(Base):
    __tablename__ = 'rooms'
    
    number = Column(String, primary_key=True)
    floor = Column(Integer)
    room_type = Column(String)
    price = Column(Float)
    amenities = Column(JSON)
    status = Column(String)

class Guest(Base):
    __tablename__ = 'guests'
    
    guest_id = Column(String, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    id_document = Column(String)
    contact_info = Column(JSON)
    is_vip = Column(Boolean, default=False)
    is_loyal_customer = Column(Boolean, default=False)
    preferences = Column(JSON)
    loyalty_tier = Column(String, default="Bronze")
    stay_history = Column(JSON)

class Reservation(Base):
    __tablename__ = 'reservations'
    
    reservation_id = Column(String, primary_key=True)
    guest_id = Column(String, ForeignKey('guests.guest_id'))
    room_number = Column(String, ForeignKey('rooms.number'))
    check_in = Column(DateTime)
    check_out = Column(DateTime)
    total_price = Column(Float)
    status = Column(String)
    
    guest = relationship("Guest")
    room = relationship("Room")

class Payment(Base):
    __tablename__ = 'payments'
    
    payment_id = Column(String, primary_key=True)
    reservation_id = Column(String, ForeignKey('reservations.reservation_id'))
    amount = Column(Float)
    payment_date = Column(DateTime)
    payment_method = Column(String)
    status = Column(String)
    
    reservation = relationship("Reservation")

class Invoice(Base):
    __tablename__ = 'invoices'
    
    invoice_id = Column(String, primary_key=True)
    reservation_id = Column(String, ForeignKey('reservations.reservation_id'))
    guest_id = Column(String, ForeignKey('guests.guest_id'))
    issue_date = Column(DateTime)
    due_date = Column(DateTime)
    total_amount = Column(Float)
    paid_amount = Column(Float)
    status = Column(String)
    line_items = Column(JSON)
    
    reservation = relationship("Reservation")
    guest = relationship("Guest")

class HousekeepingTask(Base):
    __tablename__ = 'housekeeping_tasks'
    
    task_id = Column(String, primary_key=True)
    room_number = Column(String, ForeignKey('rooms.number'))
    assigned_to = Column(String)
    due_date = Column(DateTime)
    status = Column(String)
    completed_date = Column(DateTime, nullable=True)
    notes = Column(String)
    
    room = relationship("Room")

class User(Base):
    __tablename__ = 'users'
    
    username = Column(String, primary_key=True)
    password = Column(String)
    role = Column(String)
    employee_id = Column(String)

class Discount(Base):
    __tablename__ = 'discounts'
    
    discount_id = Column(String, primary_key=True)
    code = Column(String)
    percentage = Column(Float)
    fixed_amount = Column(Float)
    valid_from = Column(DateTime, nullable=True)
    valid_to = Column(DateTime, nullable=True)
    min_stay_days = Column(Integer)
    applicable_room_types = Column(JSON)
    applicable_guest_ids = Column(JSON)
    is_active = Column(Boolean)
    description = Column(String)
    applicable_loyalty_tiers = Column(JSON) 
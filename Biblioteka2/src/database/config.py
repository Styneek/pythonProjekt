from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

#sluzy do pobierania zmiennych srodowiskowych, jesli jest zwraca 1 arg, jak nie to wartosc domysla 2 arg
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///hotel.db') 

engine = create_engine(DATABASE_URL) #komunikacja z baza

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) #sluzy do tworzenia sesji polaczen

Base = declarative_base() #dzieki Base mozna zdefiniowac klasy python, ktore odpowadaja tabela bazy

#tworze sesje polaczenia
def get_db():
    db = SessionLocal()
    try:
        yield db #dla api/zaleznosci
    finally:
        db.close()
from .models import Base
from .config import engine
import logging

logger = logging.getLogger('hotel_reservation_app')


def init_database():
    try:
        Base.metadata.create_all(engine) #zawiera wszystkie dane o modelach tabele/kolumny/relacje i tworzy fizycznie tabele
        logger.info("Tabele zostay stworzone poprawnie")
    except Exception as e:
        logger.error(f"Error podczas tworzenia tabel: {str(e)}")
        raise #zlapanie bledu ^

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO) #bede widoczne logi/bledy
    
    init_database() #wywolanie funkcji ktora tworzy tabele
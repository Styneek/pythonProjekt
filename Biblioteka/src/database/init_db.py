from .models import Base
from .config import engine
import logging

logger = logging.getLogger('hotel_reservation_app')

def init_database():
    try:
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    init_database() 
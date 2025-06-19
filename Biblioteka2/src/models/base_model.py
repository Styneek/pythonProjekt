from abc import ABC, abstractmethod

class BaseModel(ABC):
    @abstractmethod
    def to_dict(self): # konwersji obiektu do słownika
        pass

    @staticmethod
    @abstractmethod
    def from_dict(data): # Służy do stworzenia instancji z danych w formie słownika
        pass 
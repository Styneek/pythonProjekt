from abc import ABC, abstractmethod

class BaseModel(ABC):
    @abstractmethod
    def to_dict(self):
        pass

    @staticmethod
    @abstractmethod
    def from_dict(data):
        pass 
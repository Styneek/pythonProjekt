import json
from src.models.base_model import BaseModel

class User(BaseModel):
    def __init__(self, username, password, role="recepcjonista", employee_id=None):
        self.username = username
        self.password = password  
        self.role = role          
        self.employee_id = employee_id

    def to_dict(self):
        return {
            "username": self.username,
            "password": self.password,
            "role": self.role,
            "employee_id": self.employee_id
        }

    @staticmethod
    def from_dict(data):
        return User(
            data["username"],
            data["password"],
            data["role"],
            data.get("employee_id")
        )

    def has_permission(self, required_role):
        role_hierarchy = {
            "pokojówka": 1,
            "recepcjonista": 2,
            "administrator": 3
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)

    def __str__(self):
        return f"Użytkownik: {self.username}, Rola: {self.role.capitalize()}, ID Pracownika: {self.employee_id if self.employee_id else 'Brak'}"

if __name__ == "__main__":
    user1 = User("admin", "adminpass", "administrator", "EMP001")
    user2 = User("recepcja", "recpass", "recepcjonista")
    user3 = User("sprzataczka", "sprzataczpass", "pokojówka")

    print(user1)
    print(user2)
    print(user3)

    print(f"Admin can manage rooms: {user1.has_permission('recepcjonista')}")
    print(f"Recepcjonista can manage rooms: {user2.has_permission('recepcjonista')}")
    print(f"Pokojówka can manage rooms: {user3.has_permission('recepcjonista')}")

    print(f"Admin can manage users: {user1.has_permission('administrator')}")
    print(f"Recepcjonista can manage users: {user2.has_permission('administrator')}")

    user_data = user1.to_dict()
    print(user_data)
    user_from_dict = User.from_dict(user_data)
    print(user_from_dict) 
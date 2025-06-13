import json
from datetime import datetime
from src.models.base_model import BaseModel

class HousekeepingTask(BaseModel):
    def __init__(self, task_id, room_number, assigned_to, due_date, status="pending", completed_date=None, notes=None):
        self.task_id = task_id
        self.room_number = room_number
        self.assigned_to = assigned_to 
        self.due_date = due_date       
        self.status = status          
        self.completed_date = completed_date
        self.notes = notes if notes is not None else ""

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "room_number": self.room_number,
            "assigned_to": self.assigned_to,
            "due_date": self.due_date,
            "status": self.status,
            "completed_date": self.completed_date,
            "notes": self.notes
        }

    @staticmethod
    def from_dict(data):
        return HousekeepingTask(
            data["task_id"],
            data["room_number"],
            data["assigned_to"],
            data["due_date"],
            data["status"],
            data.get("completed_date"),
            data.get("notes")
        )

    def update_status(self, new_status, completed_date=None):
        valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
        if new_status in valid_statuses:
            self.status = new_status
            if new_status == "completed" and completed_date is None:
                self.completed_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elif completed_date is not None:
                self.completed_date = completed_date
            return True
        return False

    def __str__(self):
        return (f"ID Zadania: {self.task_id}, Pokój: {self.room_number}, Przypisane do: {self.assigned_to}, "
                f"Termin: {self.due_date}, Status: {self.status}")

if __name__ == "__main__":
    task1 = HousekeepingTask("HKT001", "101", "John Doe", "2023-06-10")
    print(task1)

    task1.update_status("in_progress")
    print(task1)

    task1.update_status("completed")
    print(task1)

    task_data = task1.to_dict()
    print(task_data)

    task2 = HousekeepingTask.from_dict(task_data)
    print(task2) 
ROOM_STATUSES = ["dostępny", "zajęty", "sprzątanie", "konserwacja", "zarezerwowany"]
ROOM_STATUS_MAPPING = {
    "dostępny": "available",
    "zajęty": "occupied",
    "sprzątanie": "cleaning",
    "konserwacja": "maintenance",
    "zarezerwowany": "reserved"
}
REVERSE_ROOM_STATUS_MAPPING = {v: k for k, v in ROOM_STATUS_MAPPING.items()}

RESERVATION_STATUSES = ["aktywna", "anulowana", "zameldowana", "wymeldowana"]
RESERVATION_STATUS_MAPPING = {
    "aktywna": "active",
    "anulowana": "cancelled",
    "zameldowana": "checked_in",
    "wymeldowana": "checked_out"
}
REVERSE_RESERVATION_STATUS_MAPPING = {v: k for k, v in RESERVATION_STATUS_MAPPING.items()}

PAYMENT_STATUSES = ["oczekująca", "opłacona", "częściowo opłacona"]
PAYMENT_STATUS_MAPPING = {
    "oczekująca": "pending",
    "opłacona": "paid",
    "częściowo opłacona": "partially_paid"
}
REVERSE_PAYMENT_STATUS_MAPPING = {v: k for k, v in PAYMENT_STATUS_MAPPING.items()}

INVOICE_STATUSES = ["oczekująca", "opłacona", "częściowo opłacona"]
INVOICE_STATUS_MAPPING = {
    "oczekująca": "pending",
    "opłacona": "paid",
    "częściowo opłacona": "partially_paid"
}
REVERSE_INVOICE_STATUS_MAPPING = {v: k for k, v in INVOICE_STATUS_MAPPING.items()}

HOUSEKEEPING_TASK_STATUSES = ["oczekujące", "w trakcie", "ukończone", "anulowane"]
HOUSEKEEPING_STATUS_MAPPING = {
    "oczekujące": "pending",
    "w trakcie": "in_progress",
    "ukończone": "completed",
    "anulowane": "cancelled"
}
REVERSE_HOUSEKEEPING_STATUS_MAPPING = {v: k for k, v in HOUSEKEEPING_STATUS_MAPPING.items()} 
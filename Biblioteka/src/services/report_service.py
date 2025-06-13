import logging
from src.data.data_manager import DataManager
from src.services.reservation_service import ReservationService
from src.services.room_service import RoomService
from datetime import datetime, timedelta
import os
import matplotlib.pyplot as plt
import csv
import pandas as pd

logger = logging.getLogger('hotel_reservation_app') 

class ReportService:
    def __init__(self, data_manager: DataManager, reservation_service: ReservationService, room_service: RoomService, guest_service, payment_service, housekeeping_service):
        self.data_manager = data_manager
        self.reservation_service = reservation_service
        self.room_service = room_service
        self.guest_service = guest_service
        self.payment_service = payment_service
        self.housekeeping_service = housekeeping_service
        logger.info("ReportService zainicjowany.")

    def generate_occupancy_report(self, date_str):
        try:
            report_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            logger.info(f"Generowanie raportu obłożenia dla daty: {date_str}")
        except ValueError as e:
            print("Błąd: Nieprawidłowy format daty. Użyj RRRR-MM-DD.")
            logger.error(f"Błąd formatu daty w generate_occupancy_report: {date_str} - {e}")
            return [], []

        all_rooms = self.room_service.rooms
        if not all_rooms:
            print("Brak zarejestrowanych pokoi w systemie.")
            logger.info("Brak zarejestrowanych pokoi w systemie, nie można wygenerować raportu obłożenia.")
            return [], []

        occupied_rooms_count = 0
        total_rooms_count = len(all_rooms)
        occupancy_details_data = [] 

        active_reservations = [res for res in self.reservation_service.reservations if res.status == "active" or res.status == "checked_in"]

        for room in all_rooms:
            room_status_for_date = "dostępny"
            current_guest_id = "N/A"
            current_reservation_id = "N/A"

            for res in active_reservations:
                if res.room_number == room.number:
                    res_check_in = datetime.strptime(res.check_in_date, "%Y-%m-%d").date()
                    res_check_out = datetime.strptime(res.check_out_date, "%Y-%m-%d").date()

                    if res_check_in <= report_date < res_check_out:
                        room_status_for_date = "zajęty"
                        occupied_rooms_count += 1
                        current_guest_id = res.guest_id
                        current_reservation_id = res.reservation_id
                        break
            occupancy_details_data.append({
                "Data": report_date.strftime("%Y-%m-%d"),
                "Numer Pokoju": room.number,
                "Typ Pokoju": room.room_type,
                "Status": room_status_for_date.capitalize(),
                "ID Rezerwacji": current_reservation_id,
                "ID Gościa": current_guest_id
            })

        occupancy_rate = (occupied_rooms_count / total_rooms_count) * 100 if total_rooms_count > 0 else 0
        occupancy_report_content = (
            f"Raport obłożenia dla {date_str}:\n"
            f"Liczba zajętych pokoi: {occupied_rooms_count}\n"
            f"Liczba wszystkich pokoi: {total_rooms_count}\n"
            f"Procent obłożenia: {occupancy_rate:.2f}%\n"
        )
        logger.info(f"Wygenerowano raport obłożenia dla {date_str}: {occupied_rooms_count}/{total_rooms_count} pokoi zajętych ({occupancy_rate:.2f}%).")
        return occupancy_report_content, occupancy_details_data

    def generate_revenue_report(self, start_date_str, end_date_str):
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            logger.info(f"Generowanie raportu przychodów od {start_date_str} do {end_date_str}.")
        except ValueError as e:
            print("Błąd: Nieprawidłowy format daty. Użyj RRRR-MM-DD.")
            logger.error(f"Błąd formatu daty w generate_revenue_report: {start_date_str}, {end_date_str} - {e}")
            return []

        if start_date > end_date:
            print("Błąd: Data początkowa nie może być późniejsza niż data końcowa.")
            logger.warning(f"Data początkowa ({start_date_str}) jest po dacie końcowej ({end_date_str}) w raporcie przychodów.")
            return []

        total_revenue = 0.0
        revenue_details_data = [] 

        all_payments = self.payment_service.payments

        for payment in all_payments:
            payment_date = datetime.strptime(payment.payment_date.split(" ")[0], "%Y-%m-%d").date() 

            if start_date <= payment_date <= end_date:
                total_revenue += payment.amount
                revenue_details_data.append({
                    "Data": payment_date.strftime("%Y-%m-%d"),
                    "ID Płatności": payment.payment_id,
                    "ID Rezerwacji": payment.reservation_id,
                    "Kwota Płatności": payment.amount,
                    "Metoda Płatności": payment.payment_method
                })
        logger.info(f"Wygenerowano raport przychodów od {start_date_str} do {end_date_str}. Całkowity przychód: {total_revenue:.2f} PLN.")
        revenue_report_content = (
            f"Raport przychodów od {start_date_str} do {end_date_str}:\n"
            f"Całkowity Przychód: {total_revenue:.2f} PLN\n"
        )
        return revenue_report_content, revenue_details_data

    def generate_cancelled_reservations_report(self, start_date_str=None, end_date_str=None):
        cancelled_reservations = [res for res in self.reservation_service.reservations if res.status == "cancelled"]
        cancelled_reservations_data = [] 

        start_date = None
        end_date = None
        try:
            if start_date_str: start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            if end_date_str: end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError as e:
            print("Błąd: Nieprawidłowy format daty. Użyj RRRR-MM-DD.")
            logger.error(f"Błąd formatu daty w generate_cancelled_reservations_report: {start_date_str}, {end_date_str} - {e}")
            return []

        if start_date and end_date and start_date > end_date:
            print("Błąd: Data początkowa nie może być późniejsza niż data końcowa.")
            logger.warning(f"Data początkowa ({start_date_str}) jest po dacie końcowej ({end_date_str}) w raporcie anulowanych rezerwacji.")
            return []

        for res in cancelled_reservations:
            res_cancel_date = datetime.strptime(res.check_in_date, "%Y-%m-%d").date() 
            
            if (start_date is None or res_cancel_date >= start_date) and \
               (end_date is None or res_cancel_date <= end_date):
                cancelled_reservations_data.append({
                    "ID Rezerwacji": res.reservation_id,
                    "ID Gościa": res.guest_id,
                    "Numer Pokoju": res.room_number,
                    "Data Zameldowania (Pierwotna)": res.check_in_date,
                    "Data Wymeldowania (Pierwotna)": res.check_out_date,
                    "Suma Rezerwacji": res.total_price
                    
                })
        logger.info(f"Wygenerowano raport anulowanych rezerwacji dla okresu {start_date_str}-{end_date_str}. Znaleziono {len(cancelled_reservations_data)} anulowanych rezerwacji.")
        cancelled_report_content = (
            f"Raport Anulowanych Rezerwacji dla okresu: {start_date_str if start_date_str else 'wszystkie'} do {end_date_str if end_date_str else 'wszystkie'}\n"
            f"Liczba anulowanych rezerwacji: {len(cancelled_reservations_data)}\n"
        )
        return cancelled_report_content, cancelled_reservations_data

    def generate_arrivals_departures_report(self, date_str):
        try:
            report_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            logger.info(f"Generowanie raportu przyjazdów i wyjazdów dla daty: {date_str}")
        except ValueError as e:
            print("Błąd: Nieprawidłowy format daty. Użyj RRRR-MM-DD.")
            logger.error(f"Błąd formatu daty w generate_arrivals_departures_report: {date_str} - {e}")
            return []

        arrivals_data = [] 
        departures_data = [] 

        active_reservations = [res for res in self.reservation_service.reservations if res.status == "active" or res.status == "checked_in"]

        for res in active_reservations:
            res_check_in = datetime.strptime(res.check_in_date, "%Y-%m-%d").date()
            res_check_out = datetime.strptime(res.check_out_date, "%Y-%m-%d").date()

            if res_check_in == report_date:
                arrivals_data.append({
                    "Typ": "Przyjazd",
                    "ID Rezerwacji": res.reservation_id,
                    "ID Gościa": res.guest_id,
                    "Numer Pokoju": res.room_number,
                    "Data": report_date.strftime("%Y-%m-%d")
                })
            if res_check_out == report_date:
                departures_data.append({
                    "Typ": "Wyjazd",
                    "ID Rezerwacji": res.reservation_id,
                    "ID Gościa": res.guest_id,
                    "Numer Pokoju": res.room_number,
                    "Data": report_date.strftime("%Y-%m-%d")
                })
        logger.info(f"Wygenerowano raport przyjazdów i wyjazdów dla {date_str}: {len(arrivals_data)} przyjazdów, {len(departures_data)} wyjazdów.")
        arrivals_departures_report_content = (
            f"Raport przyjazdów i wyjazdów dla daty: {date_str}\n"
            f"Liczba przyjazdów: {len(arrivals_data)}\n"
            f"Liczba wyjazdów: {len(departures_data)}\n"
        )
        return arrivals_departures_report_content, arrivals_data + departures_data

    def generate_room_statistics(self, rooms):
        logger.info("Generowanie statystyk pokoi.")
        if not rooms:
            logger.info("Brak danych pokoi do wygenerowania statystyk.")
            return {}

        room_type_counts = {}
        total_price_by_type = {}
        for room in rooms:
            room_type_counts[room.room_type] = room_type_counts.get(room.room_type, 0) + 1
            total_price_by_type[room.room_type] = total_price_by_type.get(room.room_type, 0) + room.price
        
        stats = {
            "Liczba wszystkich pokoi": len(rooms),
            "Liczba pokoi według typu": room_type_counts,
            "Średnia cena za typ pokoju": {rt: total_price_by_type[rt] / count for rt, count in room_type_counts.items()}
        }
        logger.info("Pomyślnie wygenerowano statystyki pokoi.")
        return stats

    def generate_guest_statistics_report(self):
        logger.info("Generowanie raportu statystyk gości.")
        all_guests = self.guest_service.list_all_guests()
        if not all_guests:
            logger.info("Brak danych gości do wygenerowania raportu statystyk.")
            return "Brak danych gości do wygenerowania raportu statystyk.", []

        total_guests = len(all_guests)
        vip_guests = [g for g in all_guests if g.is_vip]
        loyal_customers = [g for g in all_guests if g.is_loyal_customer]

        loyalty_tier_counts = {}
        for guest in all_guests:
            tier = guest.loyalty_tier 
            loyalty_tier_counts[tier] = loyalty_tier_counts.get(tier, 0) + 1
        
        preference_counts = {}
        for guest in all_guests:
            if hasattr(guest, 'preferences') and isinstance(guest.preferences, list):
                for pref in guest.preferences:
                    preference_counts[pref] = preference_counts.get(pref, 0) + 1

        report_content = (
            f"Raport Statystyk Gości:\n"
            f"Całkowita liczba gości: {total_guests}\n"
            f"Goście VIP: {len(vip_guests)}\n"
            f"Lojalni klienci: {len(loyal_customers)}\n"
            f"Statystyki poziomów lojalności: {loyalty_tier_counts}\n"
        )

        structured_data = [
            {"Typ Statystyki": "Całkowita liczba gości", "Wartość": total_guests},
            {"Typ Statystyki": "Goście VIP", "Wartość": len(vip_guests)},
            {"Typ Statystyki": "Lojalni klienci", "Wartość": len(loyal_customers)}
        ]
        for tier, count in loyalty_tier_counts.items():
            structured_data.append({"Typ Statystyki": f"Poziom Lojalności: {tier}", "Wartość": count})
        for pref, count in preference_counts.items():
            structured_data.append({"Typ Statystyki": f"Preferencja: {pref}", "Wartość": count})

        logger.info("Pomyślnie wygenerowano raport statystyk gości.")
        return report_content, structured_data

    def generate_housekeeping_report(self):
        logger.info("Generowanie raportu zadań sprzątania.")
        all_tasks = self.housekeeping_service.list_all_tasks()
        if not all_tasks:
            logger.info("Brak danych zadań sprzątania do wygenerowania raportu.")
            return "Brak danych zadań sprzątania do wygenerowania raportu.", []

        total_tasks = len(all_tasks)
        pending_tasks = [t for t in all_tasks if t.status == "pending"]
        in_progress_tasks = [t for t in all_tasks if t.status == "in_progress"]
        completed_tasks = [t for t in all_tasks if t.status == "completed"]
        cancelled_tasks = [t for t in all_tasks if t.status == "cancelled"]

        report_content = (
            f"Raport Zadań Sprzątania:\n"
            f"Całkowita liczba zadań: {total_tasks}\n"
            f"Zadania oczekujące: {len(pending_tasks)}\n"
            f"Zadania w trakcie: {len(in_progress_tasks)}\n"
            f"Zadania ukończone: {len(completed_tasks)}\n"
            f"Zadania anulowane: {len(cancelled_tasks)}\n"
        )

        structured_data = []
        for task in all_tasks:
            structured_data.append({
                "task_id": task.task_id,
                "room_number": task.room_number,
                "assigned_to": task.assigned_to,
                "due_date": task.due_date,
                "status": task.status,
                "notes": task.notes
            })

        logger.info("Pomyślnie wygenerowano raport zadań sprzątania.")
        return report_content, structured_data

    def plot_occupancy_by_room_type(self, rooms):
        logger.info("Generowanie wizualizacji obłożenia pokoi według typu.")
        if not rooms:
            print("Brak danych pokoi do wygenerowania wykresu.")
            logger.warning("Brak danych pokoi do wygenerowania wykresu obłożenia.")
            return False

        room_type_counts = {}
        for room in rooms:
            room_type_counts[room.room_type] = room_type_counts.get(room.room_type, 0) + 1

        labels = room_type_counts.keys()
        sizes = room_type_counts.values()
        colors = plt.cm.Paired(range(len(labels)))

        fig1, ax1 = plt.subplots()
        wedges, texts, autotexts = ax1.pie(sizes, colors=colors, autopct=lambda p: f'{p:.1f}%',
                                        startangle=90, pctdistance=0.85)

        ax1.axis('equal')  
        
        plt.setp(autotexts, size=8, weight="bold")
        ax1.legend(wedges, labels, title="Typy Pokoi", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        plt.title("Obłożenie Pokoi według Typu")
        plt.tight_layout()
        plt.show()
        logger.info("Wizualizacja obłożenia pokoi według typu została wygenerowana i wyświetlona.")
        return True
    
    def export_to_csv(self, data, filename):
        if not data:
            print("Brak danych do eksportu do CSV.")
            logger.warning(f"Brak danych do eksportu do CSV dla pliku {filename}.")
            return False
        
        keys = data[0].keys()
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as output_file:
                dict_writer = csv.DictWriter(output_file, keys)
                dict_writer.writeheader()
                dict_writer.writerows(data)
            logger.info(f"Dane pomyślnie wyeksportowane do CSV: {filename}")
            return True
        except IOError as e:
            print(f"Błąd zapisu do pliku CSV {filename}: {e}")
            logger.error(f"Błąd zapisu do pliku CSV {filename}: {e}")
            return False

    def export_to_excel(self, data, filename):
        if not data:
            print("Brak danych do eksportu do Excela.")
            logger.warning(f"Brak danych do eksportu do Excela dla pliku {filename}.")
            return False
        
        try:
            df = pd.DataFrame(data)
            df.to_excel(filename, index=False, engine='openpyxl')
            logger.info(f"Dane pomyślnie wyeksportowane do Excela: {filename}")
            return True
        except Exception as e:
            print(f"Błąd zapisu do pliku Excel {filename}: {e}")
            logger.error(f"Błąd zapisu do pliku Excel {filename}: {e}")
            return False

    def export_report_to_file(self, content, filename):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Raport został pomyślnie wyeksportowany do pliku {filename}")
            logger.info(f"Raport został pomyślnie wyeksportowany do pliku {filename}")
            return True
        except IOError as e:
            print(f"Błąd podczas eksportu raportu do pliku {filename}: {e}")
            logger.error(f"Błąd podczas eksportu raportu do pliku {filename}: {e}")
            return False

if __name__ == "__main__":
    dm = DataManager()
    room_service = type("RoomService", (object,), {"list_all_rooms": lambda self: [type("Room", (object,), {"number": "101", "room_type": "single"})(), type("Room", (object,), {"number": "102", "room_type": "double"})()]})() 
    guest_service = type("GuestService", (object,), {"add_guest": lambda self, *args, **kwargs: None})() 

    class MockReservation:
        def __init__(self, reservation_id, guest_id, room_number, check_in_date, check_out_date, total_price, status):
            self.reservation_id = reservation_id
            self.guest_id = guest_id
            self.room_number = room_number
            self.check_in_date = check_in_date
            self.check_out_date = check_out_date
            self.total_price = total_price
            self.status = status

    class MockReservationService:
        def __init__(self, reservations):
            self.reservations = reservations

    dummy_reservations = [
        MockReservation("RES001", "G001", "101", "2023-05-10", "2023-05-15", 500.00, "active"),
        MockReservation("RES002", "G002", "102", "2023-05-12", "2023-05-18", 600.00, "active"),
        MockReservation("RES003", "G001", "103", "2023-05-01", "2023-05-05", 400.00, "completed"),
        MockReservation("RES004", "G003", "101", "2023-05-20", "2023-05-25", 500.00, "cancelled"),
    ]
    reservation_service = MockReservationService(dummy_reservations)

    report_service = ReportService(dm, reservation_service, room_service, guest_service, None, None)

    print("\n--- Generowanie Raportów ---")
    report_service.generate_occupancy_report("2023-05-13")
    report_service.generate_revenue_report("2023-05-01", "2023-05-31")
    report_service.generate_cancelled_reservations_report()
    report_service.generate_arrivals_departures_report("2023-05-10")
    report_service.generate_arrivals_departures_report("2023-05-15")

    occupancy_report_content, occupancy_details_data = report_service.generate_occupancy_report("2023-05-14")
    if occupancy_report_content:
        report_service.export_report_to_file(occupancy_report_content, "raport_oblozenia_2023-05-14.txt")
        print("Raport obłożenia został pomyślnie wyeksportowany do pliku raport_oblozenia_2023-05-14.txt")

    if occupancy_details_data:
        print("Raport obłożenia został pomyślnie wyeksportowany do pliku raport_oblozenia_2023-05-14_data.csv")
        report_service.export_to_file(pd.DataFrame(occupancy_details_data).to_csv(index=False), "raport_oblozenia_2023-05-14_data.csv") 
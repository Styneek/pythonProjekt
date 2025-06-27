import logging
from datetime import datetime, timedelta
import os
import matplotlib.pyplot as plt
import csv
import pandas as pd
from src.constants.status_mappings import REVERSE_HOUSEKEEPING_STATUS_MAPPING

logger = logging.getLogger('hotel_reservation_app') 

class ReportService:
    def __init__(self, reservation_service, room_service, guest_service, payment_service, housekeeping_service):
        #tworze dostep do:
        self.reservation_service = reservation_service
        self.room_service = room_service
        self.guest_service = guest_service
        self.payment_service = payment_service
        self.housekeeping_service = housekeeping_service
        logger.info("ReportService zainicjowany (DB).")

    def generate_occupancy_report(self, date_str):
        try:
            report_date = datetime.strptime(date_str, "%Y-%m-%d").date()#przyjmuje date/konwertuje
            logger.info(f"Generowanie raportu obłożenia dla daty: {date_str}")
        except ValueError as e:
            print("Błąd: Nieprawidłowy format daty. Użyj RRRR-MM-DD.")
            logger.error(f"Błąd formatu daty w generate_occupancy_report: {date_str} - {e}")
            return [], []#zla data/ brak pokoi

        all_rooms = self.room_service.list_all_rooms()
        if not all_rooms:
            print("Brak zarejestrowanych pokoi w systemie.")
            logger.info("Brak zarejestrowanych pokoi w systemie, nie można wygenerować raportu obłożenia.")
            return [], []#zla data/ brak pokoi

        occupied_rooms_count = 0
        total_rooms_count = len(all_rooms)
        occupancy_details_data = [] 

        active_reservations = [res for res in self.reservation_service.list_all_reservations() if res.status in ["active", "checked_in"]]#pobierma tylko te ktore sa avtive/checked_in

        for room in all_rooms:
            room_status_for_date = "dostępny"
            current_guest_id = "N/A"
            current_reservation_id = "N/A"

            for res in active_reservations:
                if res.room_number == room.number:#jesli dotyczy danego pokoju/ stringi na date
                    res_check_in = res.check_in.date() if hasattr(res.check_in, 'date') else res.check_in
                    res_check_out = res.check_out.date() if hasattr(res.check_out, 'date') else res.check_out
                    if res_check_in <= report_date < res_check_out:#jesli data raportu <w> czasie rezerwaci pokoj zajety
                        room_status_for_date = "zajęty"
                        occupied_rooms_count += 1
                        current_guest_id = res.guest_id
                        current_reservation_id = res.reservation_id
                        break
                    #dodaje do szczegolow
            occupancy_details_data.append({
                "Data": report_date.strftime("%Y-%m-%d"),
                "Numer Pokoju": room.number,
                "Typ Pokoju": room.room_type,
                "Status": room_status_for_date.capitalize(),
                "ID Rezerwacji": current_reservation_id,
                "ID Gościa": current_guest_id
            })
        #% oblozenie
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

        all_payments = self.payment_service.list_all_payments()

        for payment in all_payments:
            payment_date = payment.payment_date.date() if hasattr(payment.payment_date, 'date') else payment.payment_date
            if start_date <= payment_date <= end_date:
                total_revenue += payment.amount#dodaje kwote platnosci do calkowitego przychodu
                #dodaje do szczegolow
                revenue_details_data.append({
                    "Data": payment_date.strftime("%Y-%m-%d"),
                    "ID Płatności": payment.payment_id,
                    "ID Rezerwacji": payment.reservation_id,
                    "Kwota Płatności": payment.amount,
                    "Metoda Płatności": payment.payment_method
                })
        logger.info(f"Wygenerowano raport przychodów od {start_date_str} do {end_date_str}. Całkowity przychód: {total_revenue:.2f} PLN.")
        #tworze podsumowanie do wyswietlenia
        revenue_report_content = (
            f"Raport przychodów od {start_date_str} do {end_date_str}:\n"
            f"Całkowity Przychód: {total_revenue:.2f} PLN\n"
        )
        return revenue_report_content, revenue_details_data

    def generate_cancelled_reservations_report(self, start_date_str=None, end_date_str=None):
        cancelled_reservations = [res for res in self.reservation_service.list_all_reservations() if res.status == "cancelled"]
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
            res_cancel_date = res.check_in.date() if hasattr(res.check_in, 'date') else res.check_in
            if (start_date is None or res_cancel_date >= start_date) and \
               (end_date is None or res_cancel_date <= end_date):
                #dodaje do listy
                cancelled_reservations_data.append({
                    "ID Rezerwacji": res.reservation_id,
                    "ID Gościa": res.guest_id,
                    "Numer Pokoju": res.room_number,
                    "Data Zameldowania (Pierwotna)": res.check_in.strftime("%Y-%m-%d") if hasattr(res.check_in, 'strftime') else res.check_in,
                    "Data Wymeldowania (Pierwotna)": res.check_out.strftime("%Y-%m-%d") if hasattr(res.check_out, 'strftime') else res.check_out,
                    "Suma Rezerwacji": res.total_price
                })
        logger.info(f"Wygenerowano raport anulowanych rezerwacji dla okresu {start_date_str}-{end_date_str}. Znaleziono {len(cancelled_reservations_data)} anulowanych rezerwacji.")
        #raport do wyswietlenia
        cancelled_report_content = (
            f"Raport Anulowanych Rezerwacji dla okresu: {start_date_str if start_date_str else 'wszystkie'} do {end_date_str if end_date_str else 'wszystkie'}\n"
            f"Liczba anulowanych rezerwacji: {len(cancelled_reservations_data)}\n"
        )
        return cancelled_report_content, cancelled_reservations_data

    def generate_arrivals_departures_report(self, date_str):#przyjazdy wyjazdy
        try:
            report_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            logger.info(f"Generowanie raportu przyjazdów i wyjazdów dla daty: {date_str}")
        except ValueError as e:
            print("Błąd: Nieprawidłowy format daty. Użyj RRRR-MM-DD.")
            logger.error(f"Błąd formatu daty w generate_arrivals_departures_report: {date_str} - {e}")
            return []

        arrivals_data = [] 
        departures_data = [] 

        active_reservations = [res for res in self.reservation_service.list_all_reservations() if res.status in ["active", "checked_in"]]

        for res in active_reservations:
            res_check_in = res.check_in.date() if hasattr(res.check_in, 'date') else res.check_in
            res_check_out = res.check_out.date() if hasattr(res.check_out, 'date') else res.check_out
            #dodaje dane o przyjezdzie
            if res_check_in == report_date:
                arrivals_data.append({
                    "Typ": "Przyjazd",
                    "ID Rezerwacji": res.reservation_id,
                    "ID Gościa": res.guest_id,
                    "Numer Pokoju": res.room_number,
                    "Data": report_date.strftime("%Y-%m-%d")
                })
            #dodaje dane o wyjezdzie
            if res_check_out == report_date:
                departures_data.append({
                    "Typ": "Wyjazd",
                    "ID Rezerwacji": res.reservation_id,
                    "ID Gościa": res.guest_id,
                    "Numer Pokoju": res.room_number,
                    "Data": report_date.strftime("%Y-%m-%d")
                })
        logger.info(f"Wygenerowano raport przyjazdów i wyjazdów dla {date_str}: {len(arrivals_data)} przyjazdów, {len(departures_data)} wyjazdów.")
        #raport do wyswietlenia
        arrivals_departures_report_content = (
            f"Raport przyjazdów i wyjazdów dla daty: {date_str}\n"
            f"Liczba przyjazdów: {len(arrivals_data)}\n"
            f"Liczba wyjazdów: {len(departures_data)}\n"
        )
        return arrivals_departures_report_content, arrivals_data, departures_data

    def generate_room_statistics(self, rooms):
        logger.info("Generowanie statystyk pokoi.")
        if not rooms:#lista pusta
            logger.info("Brak danych pokoi do wygenerowania statystyk.")
            return {}

        room_type_counts = {}
        total_price_by_type = {}
        #licze ile pokoi jakiego typu/ sumuje ceny
        for room in rooms:
            room_type_counts[room.room_type] = room_type_counts.get(room.room_type, 0) + 1
            total_price_by_type[room.room_type] = total_price_by_type.get(room.room_type, 0) + room.price
        #wynikowy slownik
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
        #odczytuje tier i dodaje
        for guest in all_guests:
            tier = guest.loyalty_tier 
            loyalty_tier_counts[tier] = loyalty_tier_counts.get(tier, 0) + 1
        
        preference_counts = {}
        for guest in all_guests:
            if hasattr(guest, 'preferences') and isinstance(guest.preferences, list):
                for pref in guest.preferences:
                    preference_counts[pref] = preference_counts.get(pref, 0) + 1#dodaje preferencje
        #podsumowanie tekstowe
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
        #dodaje dane o lojalnosci
        for tier, count in loyalty_tier_counts.items():
            structured_data.append({"Typ Statystyki": f"Poziom Lojalności: {tier}", "Wartość": count})
        #dodaje dane o preferencjach
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

        total_tasks = len(all_tasks)#calkowita liczba zadan
        #kazdy status osobna lista
        pending_tasks = [t for t in all_tasks if t.status == "pending"]
        in_progress_tasks = [t for t in all_tasks if t.status == "in_progress"]
        completed_tasks = [t for t in all_tasks if t.status == "completed"]
        cancelled_tasks = [t for t in all_tasks if t.status == "cancelled"]

        #raport tekstowy
        report_content = (
            f"Raport Zadań Sprzątania:\n"
            f"Całkowita liczba zadań: {total_tasks}\n"
            f"Zadania oczekujące: {len(pending_tasks)}\n"
            f"Zadania w trakcie: {len(in_progress_tasks)}\n"
            f"Zadania ukończone: {len(completed_tasks)}\n"
            f"Zadania anulowane: {len(cancelled_tasks)}\n"
        )
        #lista szczegolow kazdego zadania
        structured_data = []
        for task in all_tasks:
            structured_data.append({
                "task_id": task.task_id,
                "room_number": task.room_number,
                "assigned_to": task.assigned_to,
                "due_date": task.due_date,
                "status": REVERSE_HOUSEKEEPING_STATUS_MAPPING.get(task.status, task.status),
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
        #kazdy element data to slownik
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


import logging
from src.models.payment import Payment
from src.models.invoice import Invoice
from src.data.data_manager import DataManager
from src.services.reservation_service import ReservationService
from datetime import datetime, timedelta

logger = logging.getLogger('hotel_reservation_app') 

class PaymentService:
    def __init__(self, data_manager: DataManager, reservation_service: ReservationService):
        self.data_manager = data_manager
        self.reservation_service = reservation_service
        
        self.payments = self.data_manager.load_payments()
        self.invoices = self.data_manager.load_invoices()
        logger.info("PaymentService zainicjowany.")

    def _save_payments(self):
        self.data_manager.save_payments(self.payments)
        logger.debug("Zapisano płatności do pliku.")

    def _save_invoices(self):
        self.data_manager.save_invoices(self.invoices)
        logger.debug("Zapisano faktury do pliku.")

    def record_payment(self, reservation_id, amount, payment_method):
        reservation = self.reservation_service.get_reservation(reservation_id)
        if not reservation:
            print(f"Błąd: Rezerwacja {reservation_id} nie znaleziono.")
            logger.warning(f"Próba zarejestrowania płatności dla nieistniejącej rezerwacji: {reservation_id}")
            return None

        payment_id = f"PAY{len(self.payments) + 1:04d}"
        payment_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payment = Payment(payment_id, reservation_id, amount, payment_date, payment_method)
        self.payments.append(payment)
        self._save_payments()
        logger.info(f"Zarejestrowano płatność {payment_id} dla rezerwacji {reservation_id}. Kwota: {amount:.2f}.")

        invoice = self.get_invoice_by_reservation_id(reservation_id)
        if invoice:
            invoice.record_payment(amount)
            self._save_invoices()
            self.reservation_service.update_reservation(reservation_id, payment_status=invoice.status)
            logger.info(f"Zaktualizowano fakturę {invoice.invoice_id} i status płatności rezerwacji {reservation_id}.")
        else:
            if amount >= reservation.total_price:
                self.reservation_service.update_reservation(reservation_id, payment_status="paid")
                logger.info(f"Rezerwacja {reservation_id} oznaczona jako opłacona (bez faktury).")
            elif amount > 0:
                self.reservation_service.update_reservation(reservation_id, payment_status="partially_paid")
                logger.info(f"Rezerwacja {reservation_id} oznaczona jako częściowo opłacona (bez faktury).")

        print(f"Płatność {payment_id} w kwocie {amount:.2f} została zarejestrowana dla rezerwacji {reservation_id}.")
        return payment

    def generate_invoice(self, reservation_id):
        reservation = self.reservation_service.get_reservation(reservation_id)
        if not reservation:
            print(f"Błąd: Rezerwacja {reservation_id} nie znaleziono.")
            logger.warning(f"Próba wygenerowania faktury dla nieistniejącej rezerwacji: {reservation_id}")
            return None
        
        if any(invoice.reservation_id == reservation_id for invoice in self.invoices):
            print(f"Faktura dla rezerwacji {reservation_id} już istnieje. Zwracam istniejącą fakturę.")
            existing_invoice = self.get_invoice_by_reservation_id(reservation_id)
            logger.info(f"Faktura dla rezerwacji {reservation_id} już istnieje ({existing_invoice.invoice_id}).")
            return existing_invoice

        invoice_id_num = len(self.invoices) + 1
        invoice_id = f"INV{invoice_id_num:04d}"
        issue_date = datetime.now().strftime("%Y-%m-%d")
        due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d") 
        total_amount = reservation.total_price

        invoice = Invoice(invoice_id, reservation_id, reservation.guest_id, issue_date, due_date, total_amount)
        invoice.add_line_item(f"Opłata za pokój (Pokój {reservation.room_number}, {reservation.check_in_date} do {reservation.check_out_date})", total_amount)

        self.invoices.append(invoice)
        self._save_invoices()
        print(f"Faktura {invoice_id} wygenerowana dla rezerwacji {reservation_id}. Suma: {total_amount:.2f}.")
        logger.info(f"Wygenerowano fakturę {invoice_id} dla rezerwacji {reservation_id}. Suma: {total_amount:.2f}.")
        return invoice

    def get_payment(self, payment_id):
        payment = next((p for p in self.payments if p.payment_id == payment_id), None)
        if payment:
            logger.debug(f"Pobrano płatność: {payment_id}")
        else:
            logger.debug(f"Nie znaleziono płatności: {payment_id}")
        return payment

    def get_invoice(self, invoice_id):
        invoice = next((i for i in self.invoices if i.invoice_id == invoice_id), None)
        if invoice:
            logger.debug(f"Pobrano fakturę: {invoice_id}")
        else:
            logger.debug(f"Nie znaleziono faktury: {invoice_id}")
        return invoice
    
    def get_invoice_by_reservation_id(self, reservation_id):
        invoice = next((i for i in self.invoices if i.reservation_id == reservation_id), None)
        if invoice:
            logger.debug(f"Pobrano fakturę dla rezerwacji: {reservation_id}")
        else:
            logger.debug(f"Nie znaleziono faktury dla rezerwacji: {reservation_id}")
        return invoice

    def print_invoice(self, invoice_id, output_format):
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            print(f"Błąd: Faktura o ID {invoice_id} nie znaleziono.")
            logger.warning(f"Próba wydrukowania nieistniejącej faktury: {invoice_id}")
            return False

        invoice_content = f"""
==================================================
                FAKTURA VAT
==================================================
ID Faktury: {invoice.invoice_id}
ID Rezerwacji: {invoice.reservation_id}
ID Gościa: {invoice.guest_id}
Data Wystawienia: {invoice.issue_date}
Termin Płatności: {invoice.due_date}
--------------------------------------------------
Pozycje Faktury:
"""
        for item in invoice.line_items:
            invoice_content += f"  - {item['description']}: {item['amount']:.2f} PLN\n"
        invoice_content += f"""
--------------------------------------------------
Suma do zapłaty: {invoice.total_amount:.2f} PLN
Zapłacono:      {invoice.paid_amount:.2f} PLN
Status Płatności: {invoice.status.replace('_', ' ').title()}
==================================================
"""

        if output_format == "txt":
            filename = f"invoice_{invoice.invoice_id}.txt"
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(invoice_content)
                print(f"Faktura zapisana do pliku: {filename}")
                logger.info(f"Zapisano fakturę {invoice.invoice_id} do pliku TXT: {filename}")
                return True
            except IOError as e:
                print(f"Błąd zapisu faktury do pliku: {e}")
                logger.error(f"Błąd zapisu faktury {invoice.invoice_id} do pliku TXT: {e}")
                return False
        elif output_format == "pdf":
            print("Generowanie PDF nie jest zaimplementowane w tej wersji. Zostanie wyświetlony podgląd tekstowy.")
            print(invoice_content)
            logger.info(f"Wyświetlono podgląd tekstowy faktury {invoice.invoice_id} (generowanie PDF niezaimplementowane).")
            return True
        else:
            print("Nieznany format wyjściowy.")
            logger.warning(f"Próba wydruku faktury w nieznanym formacie: {output_format}")
            return False

    def list_all_payments(self):
        if not self.payments:
            print("Brak zarejestrowanych płatności.")
            logger.info("Brak zarejestrowanych płatności do wyświetlenia.")
            return []
        logger.info("Wyświetlono wszystkie płatności.")
        return self.payments

    def list_all_invoices(self):
        if not self.invoices:
            print("Brak wygenerowanych faktur.")
            logger.info("Brak wygenerowanych faktur do wyświetlenia.")
            return []
        logger.info("Wyświetlono wszystkie faktury.")
        return self.invoices

    def get_outstanding_invoices(self):
        outstanding = [i for i in self.invoices if i.status in ["pending", "partially_paid"]]
        if not outstanding:
            print("Brak nieuregulowanych faktur.")
            logger.info("Brak nieuregulowanych faktur.")
        else:
            logger.info(f"Znaleziono {len(outstanding)} nieuregulowanych faktur.")
        return outstanding

if __name__ == "__main__":
    dm = DataManager()
    room_service = type("RoomService", (object,), {"get_room": lambda self, num: type("Room", (object,), {"price": 100})("temp")})() 
    guest_service = type("GuestService", (object,), {"get_guest": lambda self, id: type("Guest", (object,), {})()})() 

    class MockReservation:
        def __init__(self, reservation_id, guest_id, room_number, check_in_date, check_out_date, total_price, payment_status):
            self.reservation_id = reservation_id
            self.guest_id = guest_id
            self.room_number = room_number
            self.check_in_date = check_in_date
            self.check_out_date = check_out_date
            self.total_price = total_price
            self.payment_status = payment_status

        def to_dict(self):
            return {
                "reservation_id": self.reservation_id,
                "guest_id": self.guest_id,
                "room_number": self.room_number,
                "check_in_date": self.check_in_date,
                "check_out_date": self.check_out_date,
                "total_price": self.total_price,
                "payment_status": self.payment_status
            }
        
        def update_status(self, new_status):
            pass 

    class MockReservationService:
        def __init__(self, reservations):
            self.reservations = reservations
        def get_reservation(self, res_id):
            return next((res for res in self.reservations if res.reservation_id == res_id), None)
        def update_reservation(self, res_id, **kwargs):
            res = self.get_reservation(res_id)
            if res: 
                for key, value in kwargs.items(): setattr(res, key, value)
                print(f"MockReservationService: Zaktualizowano rezerwację {res_id} o {kwargs}")
                return res
            return None
        def _save_reservations(self):
            pass 


    dummy_res = MockReservation("RES001", "G001", "101", "2023-06-01", "2023-06-05", 400.00, "pending")
    reservation_service = MockReservationService([dummy_res])

    payment_service = PaymentService(dm, reservation_service)

    print("\n--- Testowanie Płatności i Fakturowania ---")

    invoice1 = payment_service.generate_invoice("RES001")
    print(invoice1)
    
    payment1 = payment_service.record_payment("RES001", 200.00, "Cash")
    print(payment1)
    print("Faktura po częściowej płatności:", payment_service.get_invoice("INV001"))
    print("Status płatności rezerwacji:", reservation_service.get_reservation("RES001").payment_status)

    payment2 = payment_service.record_payment("RES001", 200.00, "Bank Transfer")
    print(payment2)
    print("Faktura po pełnej płatności:", payment_service.get_invoice("INV001"))
    print("Status płatności rezerwacji:", reservation_service.get_reservation("RES001").payment_status)

    print("\nWszystkie płatności:")
    payment_service.list_all_payments()

    print("\nWszystkie faktury:")
    payment_service.list_all_invoices()

    print("\nNieuregulowane faktury:")
    payment_service.get_outstanding_invoices()

    payment_service.generate_invoice("RES999")

    payment_service.record_payment("RES999", 50.00, "Credit Card") 
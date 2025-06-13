
from fpdf import FPDF
import os
from datetime import datetime

class PDFReportGenerator(FPDF):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.set_auto_page_break(auto=True, margin=15)

        font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DejaVuSans.ttf")
        self.add_font("DejaVu", "", font_path, uni=True)

    def header(self):
        self.set_font("DejaVu", "", 10)
        self.cell(0, 10, f"Raport tras turystycznych - {datetime.now().strftime('%Y-%m-%d')}", 0, 1, 'C')
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "", 9)
        self.cell(0, 10, f"Strona {self.page_no()}", 0, 0, 'C')

    def add_title_page(self, title, subtitle=""):
        self.add_page()
        self.set_font("DejaVu", "", 24)
        self.cell(0, 20, title, ln=True, align='C')
        self.set_font("DejaVu", "", 14)
        self.cell(0, 10, subtitle, ln=True, align='C')
        self.ln(10)
        self.set_font("DejaVu", "", 10)
        self.cell(0, 10, f"Data generowania: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')

    def add_section(self, title):
        self.add_page()
        self.set_font("DejaVu", "", 16)
        self.cell(0, 10, title, ln=True)
        self.ln(5)

    def add_paragraph(self, text):
        self.set_font("DejaVu", "", 12)
        self.multi_cell(0, 10, text)
        self.ln(5)

    def add_image(self, image_path, w=180):
        if os.path.exists(image_path):
            self.image(image_path, w=w)
            self.ln(5)

    def add_table(self, headers, data_rows):
        self.set_font("DejaVu", "", 12)
        col_widths = [60, 45, 30, 30, 30]  

        for i, header in enumerate(headers):
            self.cell(col_widths[i], 10, str(header), border=1, ln=0)
        self.ln()

        self.set_font("DejaVu", "", 11)

        for row in data_rows:
            max_height = 10
            y_start = self.get_y()
            x_start = self.get_x()

            for i, item in enumerate(row):
                self.multi_cell(col_widths[i], 10, str(item), border=1, align='L')
                x_start += col_widths[i]
                self.set_xy(x_start, y_start)
            self.ln(max_height)

    def save(self):
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        self.output(self.filename)

    def add_summary_section(self, text):
        self.add_section("Podsumowanie")
        self.add_paragraph(text)

    def add_route_details(self, route, extracted):
        self.add_section(route.name)
        self.add_paragraph(f"Region: {route.region}")
        self.add_paragraph(f"Długość: {route.lengthKm} km")
        self.add_paragraph(f"Trudność: {route.difficulty}")
        self.add_paragraph(f"Średni czas przejścia: {extracted.get('time_estimate_minutes', 'Brak danych')} minut")
        self.add_paragraph(f"Ostrzeżenia: {', '.join(extracted.get('warnings', [])) or 'Brak'}")

        gps_coords = extracted.get('gps')
        if gps_coords:
            gps_text = ', '.join([f"{lat} {lon}" for lat, lon in gps_coords])
            self.add_paragraph(f"Początek trasy: {gps_text} - koniec trasy")

        self.add_paragraph(f"Wysokości: {', '.join(map(str, extracted.get('elevations', []))) or 'Brak'} m n.p.m.")
        
        self.add_paragraph("Recenzje użytkowników:")
        for review in route.reviewInsights:
            self.add_paragraph(
                f"{review['author']} ({review.get('date')}): "
                f"{self.render_stars(review.get('rating'))} – {review['sentiment'].capitalize()}\n"
                f"{review['text']}"
            )
        self.ln(5)

    def render_stars(self, rating, max_stars=5):
        full = "★" * rating
        empty = "☆" * (max_stars - rating)
        return full + empty

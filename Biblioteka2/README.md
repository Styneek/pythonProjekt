# System Rezerwacji i Zarządzania Hotelami

Ta aplikacja konsolowa służy do zarządzania operacjami hotelowymi, w tym rezerwacjami pokoi, zarządzaniem gośćmi, monitorowaniem dostępności pokoi oraz raportowaniem finansowym.

## Funkcjonalności:

- Zarządzanie pokojami (dodawanie, edycja, usuwanie, aktualizacja statusów)
- System rezerwacji (tworzenie, modyfikowanie, anulowanie rezerwacji)
- Zarządzanie danymi gości (dane osobowe, historia pobytów, oznaczanie VIP/stałych klientów)
- Obsługa płatności i fakturowanie
- Procedury zameldowania/wymeldowania
- Raportowanie (dzienne obłożenie, przychody, anulacje, przyjazdy/wyjazdy)
- Funkcje wyszukiwania i filtrowania
- Zarządzanie harmonogramem sprzątania
- System użytkowników i uprawnień
- System rabatów i promocji

## Instalacja

1.  **Sklonuj repozytorium:**

    ```bash
    git clone https://github.com/Styneek/pythonProjekt
    cd hotel_reservation_system
    ```

2.  **Utwórz i aktywuj wirtualne środowisko:**

    ```bash
    python -m venv venv
    # Na Windows:
    .\venv\Scripts\activate
    # Na macOS/Linux:
    source venv/bin/activate
    ```

3.  **Zainstaluj zależności:**
    ```bash
    pip install -r requirements.txt
    ```

## Użycie

Aby uruchomić aplikację:

```bash
python main.py
```
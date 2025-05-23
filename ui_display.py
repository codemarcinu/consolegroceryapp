from datetime import datetime
from typing import List, Dict, Any
from tabulate import tabulate
from colorama import init, Fore, Style
from models import Produkt
from config import KONFIGURACJA

# Inicjalizacja colorama
init()

class UIDisplay:
    """
    Klasa zarządzająca interfejsem użytkownika.
    """
    
    def __init__(self):
        """
        Inicjalizuje wyświetlacz UI.
        """
        self.kolory_wlaczone = KONFIGURACJA["interface"]["colors_enabled"]
        self.format_tabeli = KONFIGURACJA["interface"]["table_format"]
    
    def wyswietl_menu(self) -> None:
        """
        Wyświetla menu główne aplikacji.
        """
        print("\n" + "=" * 40)
        print("=== ASYSTENT ZAKUPÓW I SPIŻARNI v2 ===")
        print("=" * 40)
        print("\n1. Dodaj produkt (szybko)")
        print("2. Przetwórz paragony z obrazów (OCR + AI)")
        print("3. Importuj przetworzone paragony do spiżarni")
        print("4. Przeglądaj spiżarnię")
        print("5. Zarządzaj produktami (zużyj/usuń)")
        print("6. Sugestie przepisów (AI)")
        print("7. Statystyki spiżarni")
        print("8. Ustawienia (TODO: do przyszłej rozbudowy)")
        print("9. Wyjście")
        print("\n" + "=" * 40)
    
    def wyswietl_produkty(self, produkty: List[Produkt]) -> None:
        """
        Wyświetla listę produktów w formie tabeli.
        
        Args:
            produkty: Lista produktów do wyświetlenia
        """
        if not produkty:
            print("\n❌ Brak produktów do wyświetlenia!")
            return
        
        # Przygotuj dane do tabeli
        naglowki = ["Nr", "Nazwa Produktu", "Kategoria", "Data ważności", "Dni do końca", "Cena (zł)"]
        dane = []
        
        for i, produkt in enumerate(produkty, 1):
            dni_do_konca = (produkt.data_waznosci - datetime.now()).days
            
            # Określ kolor na podstawie dni do końca
            if self.kolory_wlaczone:
                if dni_do_konca <= KONFIGURACJA["notifications"]["expiry_warning_days_critical"]:
                    kolor = Fore.RED
                elif dni_do_konca <= KONFIGURACJA["notifications"]["expiry_warning_days_warning"]:
                    kolor = Fore.YELLOW
                else:
                    kolor = Fore.GREEN
            else:
                kolor = ""
            
            # Przygotuj wiersz
            wiersz = [
                i,
                f"{kolor}{produkt.nazwa}{Style.RESET_ALL if self.kolory_wlaczone else ''}",
                produkt.kategoria,
                produkt.data_waznosci.strftime("%Y-%m-%d"),
                f"{kolor}{dni_do_konca}{Style.RESET_ALL if self.kolory_wlaczone else ''}",
                f"{produkt.cena:.2f}" if produkt.cena else "-"
            ]
            dane.append(wiersz)
        
        # Wyświetl tabelę
        print("\n" + tabulate(dane, headers=naglowki, tablefmt=self.format_tabeli))
    
    def wyswietl_statystyki(self, produkty: List[Produkt]) -> None:
        """
        Wyświetla statystyki spiżarni.
        
        Args:
            produkty: Lista wszystkich produktów
        """
        if not produkty:
            print("\n❌ Brak produktów w spiżarni!")
            return
        
        # Filtruj tylko aktywne produkty
        produkty_aktywne = [p for p in produkty if not p.zuzyty]
        
        # Oblicz statystyki
        liczba_produktow = len(produkty_aktywne)
        produkty_wygasajace = [
            p for p in produkty_aktywne
            if (p.data_waznosci - datetime.now()).days <= KONFIGURACJA["notifications"]["expiry_warning_days_critical"]
        ]
        liczba_wygasajacych = len(produkty_wygasajace)
        
        # Oblicz wartość produktów
        wartosc_produktow = sum(p.cena for p in produkty_aktywne if p.cena is not None)
        
        # Oblicz najczęstsze kategorie
        kategorie = {}
        for p in produkty_aktywne:
            kategorie[p.kategoria] = kategorie.get(p.kategoria, 0) + 1
        najczestsze_kategorie = sorted(
            kategorie.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Wyświetl statystyki
        print("\n=== STATYSTYKI SPIŻARNI ===")
        print(f"\nLiczba produktów: {liczba_produktow}")
        print(f"Produkty wygasające w ciągu {KONFIGURACJA['notifications']['expiry_warning_days_critical']} dni: {liczba_wygasajacych}")
        print(f"Szacunkowa wartość produktów: {wartosc_produktow:.2f} zł")
        
        print("\nNajczęstsze kategorie:")
        for kategoria, liczba in najczestsze_kategorie:
            print(f"- {kategoria}: {liczba} produktów")
    
    def wyswietl_sugestie_przepisow(self, sugestie: List[Dict[str, Any]]) -> None:
        """
        Wyświetla sugestie przepisów.
        
        Args:
            sugestie: Lista sugestii przepisów
        """
        if not sugestie:
            print("\n❌ Brak sugestii przepisów!")
            return
        
        print("\n=== SUGESTIE PRZEPISÓW ===")
        for i, sugestia in enumerate(sugestie, 1):
            print(f"\n{i}. {sugestia['nazwa']}")
            print("\nSkładniki:")
            for skladnik in sugestia['skladniki']:
                print(f"- {skladnik}")
            print("\nPrzygotowanie:")
            print(sugestia['przygotowanie'])
            print("\n" + "-" * 40)
    
    def wyswietl_komunikat(self, komunikat: str, typ: str = "info") -> None:
        """
        Wyświetla komunikat z odpowiednim formatowaniem.
        
        Args:
            komunikat: Tekst komunikatu
            typ: Typ komunikatu (info, sukces, blad, ostrzezenie)
        """
        if self.kolory_wlaczone:
            if typ == "sukces":
                print(f"\n{Fore.GREEN}✓ {komunikat}{Style.RESET_ALL}")
            elif typ == "blad":
                print(f"\n{Fore.RED}❌ {komunikat}{Style.RESET_ALL}")
            elif typ == "ostrzezenie":
                print(f"\n{Fore.YELLOW}⚠️ {komunikat}{Style.RESET_ALL}")
            else:
                print(f"\n{komunikat}")
        else:
            print(f"\n{komunikat}")
    
    def pobierz_wybor_menu(self) -> str:
        """
        Pobiera wybór użytkownika z menu.
        
        Returns:
            str: Wybrana opcja
        """
        while True:
            try:
                wybor = input("\nWybierz opcję (1-9): ").strip()
                if wybor.isdigit() and 1 <= int(wybor) <= 9:
                    return wybor
                else:
                    print("❌ Nieprawidłowy wybór! Wybierz liczbę od 1 do 9.")
            except ValueError:
                print("❌ Nieprawidłowy wybór! Wybierz liczbę od 1 do 9.") 
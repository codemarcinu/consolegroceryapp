from datetime import datetime
from typing import List, Optional, Dict, Any
from models import Produkt
from storage_manager import StorageManager
from llm_integration import sugeruj_kategorie, sugeruj_date_waznosci
from config import KONFIGURACJA, KATEGORIE

class ProductManager:
    """
    Klasa zarządzająca operacjami na produktach.
    """
    
    def __init__(self, storage_manager: Optional[StorageManager] = None):
        """
        Inicjalizuje menedżer produktów.
        
        Args:
            storage_manager: Opcjonalny menedżer przechowywania danych
        """
        self.storage_manager = storage_manager or StorageManager()
    
    def dodaj_szybki_produkt(self, konfiguracja_llm: Dict[str, Any]) -> bool:
        """
        Umożliwia szybkie dodanie pojedynczego produktu.
        
        Args:
            konfiguracja_llm: Konfiguracja LLM
            
        Returns:
            bool: True jeśli dodanie się powiodło, False w przeciwnym razie
        """
        try:
            # Pobierz nazwę produktu
            nazwa = input("\nPodaj nazwę produktu: ").strip()
            if not nazwa:
                print("❌ Nazwa produktu nie może być pusta!")
                return False
            
            # Sugeruj kategorię
            if konfiguracja_llm.get("auto_categorize", True):
                sugerowana_kategoria = sugeruj_kategorie(nazwa, konfiguracja_llm)
                print(f"\nSugerowana kategoria: {sugerowana_kategoria}")
                print("\nDostępne kategorie:")
                for i, kat in enumerate(KATEGORIE, 1):
                    print(f"{i}. {kat}")
                
                while True:
                    try:
                        wybor = input("\nWybierz kategorię (numer lub nazwa, Enter dla sugerowanej): ").strip()
                        if not wybor:
                            kategoria = sugerowana_kategoria
                            break
                        elif wybor.isdigit() and 1 <= int(wybor) <= len(KATEGORIE):
                            kategoria = KATEGORIE[int(wybor) - 1]
                            break
                        elif wybor in KATEGORIE:
                            kategoria = wybor
                            break
                        else:
                            print("❌ Nieprawidłowy wybór!")
                    except ValueError:
                        print("❌ Nieprawidłowy wybór!")
            else:
                kategoria = "Inne"
            
            # Sugeruj datę ważności
            if konfiguracja_llm.get("auto_expiry_date", True):
                sugerowana_data = sugeruj_date_waznosci(nazwa, kategoria, konfiguracja_llm)
                print(f"\nSugerowana data ważności: {sugerowana_data.strftime('%Y-%m-%d')}")
                
                while True:
                    try:
                        data_str = input("\nPodaj datę ważności (YYYY-MM-DD, Enter dla sugerowanej): ").strip()
                        if not data_str:
                            data_waznosci = sugerowana_data
                            break
                        data_waznosci = datetime.strptime(data_str, "%Y-%m-%d")
                        break
                    except ValueError:
                        print("❌ Nieprawidłowy format daty! Użyj YYYY-MM-DD")
            else:
                data_waznosci = datetime.now() + datetime.timedelta(days=7)
            
            # Pobierz cenę (opcjonalnie)
            while True:
                cena_str = input("\nPodaj cenę (opcjonalnie, Enter aby pominąć): ").strip()
                if not cena_str:
                    cena = None
                    break
                try:
                    cena = float(cena_str.replace(',', '.'))
                    if cena < 0:
                        print("❌ Cena nie może być ujemna!")
                        continue
                    break
                except ValueError:
                    print("❌ Nieprawidłowy format ceny!")
            
            # Utwórz i zapisz produkt
            produkt = Produkt(
                nazwa=nazwa,
                kategoria=kategoria,
                data_waznosci=data_waznosci,
                cena=cena
            )
            
            return self.storage_manager.dodaj_produkt(produkt)
            
        except Exception as e:
            print(f"❌ Błąd podczas dodawania produktu: {e}")
            return False
    
    def importuj_przetworzone_paragony(self, konfiguracja_llm: Dict[str, Any]) -> bool:
        """
        Importuje produkty z przetworzonych paragonów.
        
        Args:
            konfiguracja_llm: Konfiguracja LLM
            
        Returns:
            bool: True jeśli import się powiódł, False w przeciwnym razie
        """
        try:
            # Znajdź pliki paragonów
            folder_danych = KONFIGURACJA["paths"]["dane_json_folder"]
            pliki_paragonow = [
                f for f in os.listdir(folder_danych)
                if f.startswith("paragon_") and f.endswith(".json")
            ]
            
            if not pliki_paragonow:
                print("❌ Nie znaleziono przetworzonych paragonów!")
                return False
            
            # Wyświetl listę paragonów
            print("\nDostępne paragony:")
            for i, plik in enumerate(pliki_paragonow, 1):
                print(f"{i}. {plik}")
            
            # Wybierz paragon
            while True:
                try:
                    wybor = input("\nWybierz paragon do importu (numer lub 'wszystkie'): ").strip()
                    if wybor.lower() == 'wszystkie':
                        wybrane_pliki = pliki_paragonow
                        break
                    elif wybor.isdigit() and 1 <= int(wybor) <= len(pliki_paragonow):
                        wybrane_pliki = [pliki_paragonow[int(wybor) - 1]]
                        break
                    else:
                        print("❌ Nieprawidłowy wybór!")
                except ValueError:
                    print("❌ Nieprawidłowy wybór!")
            
            # Importuj produkty z wybranych paragonów
            for plik in wybrane_pliki:
                sciezka_pliku = os.path.join(folder_danych, plik)
                with open(sciezka_pliku, 'r', encoding='utf-8') as f:
                    dane_paragonu = json.load(f)
                
                produkty = dane_paragonu.get('produkty_ai', [])
                for produkt_dane in produkty:
                    nazwa = produkt_dane['nazwa']
                    cena = produkt_dane.get('cena')
                    
                    # Sugeruj kategorię
                    if konfiguracja_llm.get("auto_categorize", True):
                        sugerowana_kategoria = sugeruj_kategorie(nazwa, konfiguracja_llm)
                        print(f"\nProdukt: {nazwa}")
                        print(f"Sugerowana kategoria: {sugerowana_kategoria}")
                        print("\nDostępne kategorie:")
                        for i, kat in enumerate(KATEGORIE, 1):
                            print(f"{i}. {kat}")
                        
                        while True:
                            try:
                                wybor = input("\nWybierz kategorię (numer lub nazwa, Enter dla sugerowanej): ").strip()
                                if not wybor:
                                    kategoria = sugerowana_kategoria
                                    break
                                elif wybor.isdigit() and 1 <= int(wybor) <= len(KATEGORIE):
                                    kategoria = KATEGORIE[int(wybor) - 1]
                                    break
                                elif wybor in KATEGORIE:
                                    kategoria = wybor
                                    break
                                else:
                                    print("❌ Nieprawidłowy wybór!")
                            except ValueError:
                                print("❌ Nieprawidłowy wybór!")
                    else:
                        kategoria = "Inne"
                    
                    # Sugeruj datę ważności
                    if konfiguracja_llm.get("auto_expiry_date", True):
                        sugerowana_data = sugeruj_date_waznosci(nazwa, kategoria, konfiguracja_llm)
                        print(f"Sugerowana data ważności: {sugerowana_data.strftime('%Y-%m-%d')}")
                        
                        while True:
                            try:
                                data_str = input("\nPodaj datę ważności (YYYY-MM-DD, Enter dla sugerowanej): ").strip()
                                if not data_str:
                                    data_waznosci = sugerowana_data
                                    break
                                data_waznosci = datetime.strptime(data_str, "%Y-%m-%d")
                                break
                            except ValueError:
                                print("❌ Nieprawidłowy format daty! Użyj YYYY-MM-DD")
                    else:
                        data_waznosci = datetime.now() + datetime.timedelta(days=7)
                    
                    # Utwórz i zapisz produkt
                    produkt = Produkt(
                        nazwa=nazwa,
                        kategoria=kategoria,
                        data_waznosci=data_waznosci,
                        cena=cena,
                        id_paragonu=plik
                    )
                    
                    if not self.storage_manager.dodaj_produkt(produkt):
                        print(f"❌ Błąd podczas dodawania produktu: {nazwa}")
                
                # Przenieś przetworzony plik do archiwum
                sciezka_archiwum = os.path.join(KONFIGURACJA["paths"]["archiwum_json"], plik)
                shutil.move(sciezka_pliku, sciezka_archiwum)
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas importu paragonów: {e}")
            return False
    
    def szybkie_zarzadzanie_produktami(self) -> bool:
        """
        Umożliwia szybkie wyszukiwanie i zarządzanie produktami.
        
        Returns:
            bool: True jeśli operacja się powiodła, False w przeciwnym razie
        """
        try:
            from fuzzywuzzy import process
            
            # Pobierz frazę wyszukiwania
            fraza = input("\nPodaj frazę do wyszukania: ").strip()
            if not fraza:
                print("❌ Fraza wyszukiwania nie może być pusta!")
                return False
            
            # Wczytaj produkty
            produkty = self.storage_manager.wczytaj_produkty()
            produkty_aktywne = [p for p in produkty if not p.zuzyty]
            
            if not produkty_aktywne:
                print("❌ Brak aktywnych produktów!")
                return False
            
            # Wyszukaj pasujące produkty
            nazwy_produktow = [p.nazwa for p in produkty_aktywne]
            wyniki = process.extract(fraza, nazwy_produktow, limit=5)
            
            if not wyniki:
                print("❌ Nie znaleziono pasujących produktów!")
                return False
            
            # Wyświetl wyniki
            print("\nZnalezione produkty:")
            for i, (nazwa, dopasowanie) in enumerate(wyniki, 1):
                produkt = next(p for p in produkty_aktywne if p.nazwa == nazwa)
                print(f"{i}. {produkt} (dopasowanie: {dopasowanie}%)")
            
            # Wybierz produkt
            while True:
                try:
                    wybor = input("\nWybierz produkt (numer): ").strip()
                    if wybor.isdigit() and 1 <= int(wybor) <= len(wyniki):
                        wybrany_produkt = next(
                            p for p in produkty_aktywne
                            if p.nazwa == wyniki[int(wybor) - 1][0]
                        )
                        break
                    else:
                        print("❌ Nieprawidłowy wybór!")
                except ValueError:
                    print("❌ Nieprawidłowy wybór!")
            
            # Wybierz akcję
            print("\nDostępne akcje:")
            print("1. Oznacz jako zużyty")
            print("2. Usuń całkowicie")
            
            while True:
                try:
                    akcja = input("\nWybierz akcję (1-2): ").strip()
                    if akcja == "1":
                        indeks = produkty.index(wybrany_produkt)
                        return self.storage_manager.oznacz_jako_zuzyty(indeks)
                    elif akcja == "2":
                        indeks = produkty.index(wybrany_produkt)
                        return self.storage_manager.usun_produkt(indeks)
                    else:
                        print("❌ Nieprawidłowy wybór!")
                except ValueError:
                    print("❌ Nieprawidłowy wybór!")
            
        except Exception as e:
            print(f"❌ Błąd podczas zarządzania produktami: {e}")
            return False 
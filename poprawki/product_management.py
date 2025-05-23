import json
import os
import shutil
import glob
from datetime import datetime, timedelta
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
            nazwa = input("\n🏷️ Podaj nazwę produktu: ").strip()
            if not nazwa:
                print("❌ Nazwa produktu nie może być pusta!")
                return False
            
            # Sugeruj kategorię
            if KONFIGURACJA["llm"]["enabled"] and konfiguracja_llm.get("auto_categorize", True):
                print("\n🤖 AI analizuje produkt...")
                sugerowana_kategoria = sugeruj_kategorie(nazwa, konfiguracja_llm)
                print(f"🤖 AI sugeruje kategorię: {sugerowana_kategoria}")
                
                potwierdz = input("Akceptujesz sugestię? (Enter=tak, n=nie, k=zmień kategorię): ").lower()
                
                if potwierdz == 'n':
                    print("⏭️ Pominięto sugestię AI")
                    kategoria = self._wybierz_kategorie_reczne()
                elif potwierdz == 'k':
                    kategoria = self._wybierz_kategorie_reczne()
                else:
                    kategoria = sugerowana_kategoria
            else:
                kategoria = self._wybierz_kategorie_reczne()
            
            # Sugeruj datę ważności
            if KONFIGURACJA["llm"]["enabled"] and konfiguracja_llm.get("auto_expiry_date", True):
                print("\n🤖 AI sugeruje datę ważności...")
                sugerowana_data = sugeruj_date_waznosci(nazwa, kategoria, konfiguracja_llm)
                print(f"🗓️ AI sugeruje datę ważności: {sugerowana_data.strftime('%Y-%m-%d')}")
                
                data_input = input("Akceptujesz? (Enter=tak, lub podaj datę YYYY-MM-DD): ").strip()
                if data_input:
                    try:
                        data_waznosci = datetime.strptime(data_input, "%Y-%m-%d")
                        # Sprawdź czy data nie jest z przeszłości
                        if data_waznosci.date() < datetime.now().date():
                            print("⚠️ Uwaga: Podana data jest z przeszłości!")
                            potwierdz = input("Czy na pewno chcesz kontynuować? (t/n): ").lower()
                            if potwierdz != 't':
                                return False
                    except ValueError:
                        print("❌ Błędny format daty, używam sugestii AI")
                        data_waznosci = sugerowana_data
                else:
                    data_waznosci = sugerowana_data
            else:
                data_waznosci = self._pobierz_date_waznosci()
            
            # Pobierz cenę (opcjonalnie)
            cena = self._pobierz_cene()
            
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
        Importuje produkty z przetworzonych paragonów do spiżarni.
        
        Args:
            konfiguracja_llm: Konfiguracja LLM
            
        Returns:
            bool: True jeśli import się powiódł, False w przeciwnym razie
        """
        try:
            # Znajdź wszystkie pliki JSON z przetworzonymi paragonami
            json_files = glob.glob(os.path.join(KONFIGURACJA["paths"]["dane_json_folder"], "paragon_*.json"))
            
            if not json_files:
                print("📁 Brak przetworzonych paragonów do importu")
                return False
            
            print(f"📋 Znaleziono {len(json_files)} przetworzonych paragonów:")
            
            # Wyświetl listę paragonów
            for i, json_file in enumerate(json_files, 1):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    nazwa_pliku = data.get('plik_zrodlowy', 'nieznany')
                    liczba_produktow = len(data.get('produkty', []))
                    data_przetworzenia = data.get('data_przetworzenia', 'nieznana')
                    
                    print(f"{i}. {nazwa_pliku} - {liczba_produktow} produktów ({data_przetworzenia})")
                    
                except Exception as e:
                    print(f"{i}. ❌ Błąd odczytu: {os.path.basename(json_file)}")
            
            print("\n0. Importuj wszystkie")
            print("99. Anuluj")
            
            try:
                wybor = input("\nWybierz paragon do importu (0-99): ")
                
                if wybor == "99":
                    return False
                elif wybor == "0":
                    # Importuj wszystkie
                    for json_file in json_files:
                        self._importuj_pojedynczy_paragon(json_file, konfiguracja_llm)
                    return True
                else:
                    idx = int(wybor) - 1
                    if 0 <= idx < len(json_files):
                        return self._importuj_pojedynczy_paragon(json_files[idx], konfiguracja_llm)
                    else:
                        print("❌ Nieprawidłowy wybór")
                        return False
                        
            except ValueError:
                print("❌ Nieprawidłowy wybór")
                return False
            
        except Exception as e:
            print(f"❌ Błąd podczas importu paragonów: {e}")
            return False
    
    def _importuj_pojedynczy_paragon(self, json_file: str, konfiguracja_llm: Dict[str, Any]) -> bool:
        """
        Importuje produkty z pojedynczego paragonu.
        
        Args:
            json_file: Ścieżka do pliku JSON z paragonem
            konfiguracja_llm: Konfiguracja LLM
            
        Returns:
            bool: True jeśli import się powiódł
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            produkty_z_paragonu = data.get('produkty', [])
            if not produkty_z_paragonu:
                print(f"⚠️ Brak produktów w {os.path.basename(json_file)}")
                return False
            
            print(f"\n📦 Import produktów z {data.get('plik_zrodlowy', 'paragonu')}:")
            
            dodano = 0
            
            for produkt_data in produkty_z_paragonu:
                nazwa = produkt_data.get('nazwa', '').strip()
                cena = produkt_data.get('cena', 0.0)
                
                if not nazwa:
                    continue
                    
                print(f"\n🏷️ Produkt: {nazwa} ({cena:.2f} zł)")
                
                # AI sugeruje kategorię
                if KONFIGURACJA["llm"]["enabled"] and konfiguracja_llm.get("auto_categorize", True):
                    kategoria = sugeruj_kategorie(nazwa, konfiguracja_llm)
                    print(f"🤖 AI sugeruje kategorię: {kategoria}")
                    
                    potwierdz = input("Akceptujesz? (Enter=tak, n=nie, k=zmień kategorię): ").lower()
                    
                    if potwierdz == 'n':
                        print("⏭️ Pominięto produkt")
                        continue
                    elif potwierdz == 'k':
                        kategoria = self._wybierz_kategorie_reczne()
                else:
                    kategoria = self._wybierz_kategorie_reczne()
                
                # AI sugeruje datę ważności
                if KONFIGURACJA["llm"]["enabled"] and konfiguracja_llm.get("auto_expiry_date", True):
                    data_waznosci = sugeruj_date_waznosci(nazwa, kategoria, konfiguracja_llm)
                    print(f"🗓️ AI sugeruje datę ważności: {data_waznosci.strftime('%Y-%m-%d')}")
                    
                    data_input = input("Akceptujesz? (Enter=tak, lub podaj datę YYYY-MM-DD): ").strip()
                    if data_input:
                        try:
                            data_waznosci = datetime.strptime(data_input, "%Y-%m-%d")
                        except ValueError:
                            print("❌ Błędny format, używam sugestii AI")
                else:
                    data_waznosci = self._pobierz_date_waznosci()
                
                # Dodaj produkt do spiżarni
                nowy_produkt = Produkt(
                    nazwa=nazwa,
                    kategoria=kategoria,
                    data_waznosci=data_waznosci,
                    cena=cena,
                    data_dodania=datetime.now(),
                    zuzyty=False,
                    id_paragonu=os.path.basename(json_file)
                )
                
                if self.storage_manager.dodaj_produkt(nowy_produkt):
                    dodano += 1
                    print(f"✅ Dodano: {nazwa}")
                else:
                    print(f"❌ Błąd podczas dodawania: {nazwa}")
            
            if dodano > 0:
                print(f"\n🎉 Zaimportowano {dodano} produktów!")
                
                # Przenieś przetworzony plik do archiwum
                os.makedirs(KONFIGURACJA["paths"]["archiwum_json"], exist_ok=True)
                archive_file = os.path.join(KONFIGURACJA["paths"]["archiwum_json"], os.path.basename(json_file))
                shutil.move(json_file, archive_file)
                print(f"📁 Paragon przeniesiony do archiwum")
                
                return True
            else:
                print("❌ Nie dodano żadnych produktów")
                return False
                
        except Exception as e:
            print(f"❌ Błąd importu: {e}")
            return False
    
    def szybkie_zarzadzanie_produktami(self) -> bool:
        """
        Umożliwia szybkie wyszukiwanie i zarządzanie produktami.
        
        Returns:
            bool: True jeśli operacja się powiodła, False w przeciwnym razie
        """
        try:
            # Pobierz frazę wyszukiwania
            fraza = input("\n🔍 Podaj frazę do wyszukania: ").strip()
            if not fraza:
                print("❌ Fraza wyszukiwania nie może być pusta!")
                return False
            
            # Wczytaj produkty
            produkty = self.storage_manager.wczytaj_produkty()
            produkty_aktywne = [p for p in produkty if not p.zuzyty]
            
            if not produkty_aktywne:
                print("❌ Brak aktywnych produktów!")
                return False
            
            # Wyszukiwanie rozmyte
            try:
                from fuzzywuzzy import fuzz
                
                wyniki = []
                for i, produkt in enumerate(produkty_aktywne):
                    podobienstwo = fuzz.partial_ratio(fraza.lower(), produkt.nazwa.lower())
                    if podobienstwo > 60:  # 60% podobieństwa
                        dni_do_konca = (produkt.data_waznosci - datetime.now()).days
                        wyniki.append((produkt, podobienstwo, dni_do_konca, i))
                
                if wyniki:
                    wyniki.sort(key=lambda x: (-x[1], x[2]))  # sortuj po podobieństwie, potem po terminie
                    
                    print(f"\n📦 Znalezione produkty dla '{fraza}':")
                    for i, (produkt, podobienstwo, dni, _) in enumerate(wyniki[:5], 1):
                        kolor = "🔴" if dni <= 3 else "🟡" if dni <= 7 else "🟢"
                        print(f"{i}. {kolor} {produkt.nazwa} ({produkt.kategoria}) - kończy się za {dni} dni")
                    
                    try:
                        wybor = input("\nWybierz numer produktu do zarządzania (Enter = anuluj): ")
                        if wybor:
                            idx = int(wybor) - 1
                            if 0 <= idx < len(wyniki):
                                wybrany_produkt, _, _, original_idx = wyniki[idx]
                                return self._zarzadzaj_produktem(wybrany_produkt, produkty)
                    except (ValueError, IndexError):
                        print("❌ Nieprawidłowy wybór")
                else:
                    print(f"❌ Nie znaleziono produktów dla '{fraza}'")
                    
            except ImportError:
                print("⚠️ Moduł fuzzywuzzy nie jest zainstalowany. Używanie prostego wyszukiwania...")
                # Proste wyszukiwanie bez fuzzywuzzy
                wyniki = [p for p in produkty_aktywne if fraza.lower() in p.nazwa.lower()]
                if wyniki:
                    print(f"\n📦 Znalezione produkty dla '{fraza}':")
                    for i, produkt in enumerate(wyniki[:5], 1):
                        dni_do_konca = (produkt.data_waznosci - datetime.now()).days
                        kolor = "🔴" if dni_do_konca <= 3 else "🟡" if dni_do_konca <= 7 else "🟢"
                        print(f"{i}. {kolor} {produkt.nazwa} ({produkt.kategoria}) - kończy się za {dni_do_konca} dni")
                    
                    try:
                        wybor = input("\nWybierz numer produktu do zarządzania (Enter = anuluj): ")
                        if wybor:
                            idx = int(wybor) - 1
                            if 0 <= idx < len(wyniki):
                                return self._zarzadzaj_produktem(wyniki[idx], produkty)
                    except (ValueError, IndexError):
                        print("❌ Nieprawidłowy wybór")
                else:
                    print(f"❌ Nie znaleziono produktów dla '{fraza}'")
            
            return False
            
        except Exception as e:
            print(f"❌ Błąd podczas zarządzania produktami: {e}")
            return False
    
    def _zarzadzaj_produktem(self, produkt: Produkt, wszystkie_produkty: List[Produkt]) -> bool:
        """
        Zarządza wybranym produktem.
        
        Args:
            produkt: Wybrany produkt
            wszystkie_produkty: Lista wszystkich produktów
            
        Returns:
            bool: True jeśli operacja się powiodła
        """
        print(f"\n📦 Zarządzanie produktem: {produkt.nazwa}")
        print("1. Oznacz jako zużyty")
        print("2. Usuń całkowicie")
        print("3. Anuluj")
        
        while True:
            try:
                akcja = input("\nWybierz akcję (1-3): ").strip()
                if akcja == "1":
                    indeks = wszystkie_produkty.index(produkt)
                    if self.storage_manager.oznacz_jako_zuzyty(indeks):
                        print(f"✅ {produkt.nazwa} oznaczony jako zużyty!")
                        return True
                    else:
                        print("❌ Błąd podczas oznaczania jako zużyty")
                        return False
                elif akcja == "2":
                    indeks = wszystkie_produkty.index(produkt)
                    if self.storage_manager.usun_produkt(indeks):
                        print(f"✅ {produkt.nazwa} usunięty całkowicie!")
                        return True
                    else:
                        print("❌ Błąd podczas usuwania")
                        return False
                elif akcja == "3":
                    return False
                else:
                    print("❌ Nieprawidłowy wybór!")
            except ValueError:
                print("❌ Nieprawidłowy wybór!")
    
    def _wybierz_kategorie_reczne(self) -> str:
        """
        Pozwala użytkownikowi wybrać kategorię ręcznie.
        
        Returns:
            str: Wybrana kategoria
        """
        print("\nDostępne kategorie:")
        for i, kat in enumerate(KATEGORIE, 1):
            print(f"{i}. {kat}")
        
        while True:
            try:
                wybor = input(f"\nWybierz kategorię (1-{len(KATEGORIE)}): ").strip()
                if wybor.isdigit() and 1 <= int(wybor) <= len(KATEGORIE):
                    return KATEGORIE[int(wybor) - 1]
                else:
                    print("❌ Nieprawidłowy wybór!")
            except ValueError:
                print("❌ Nieprawidłowy wybór!")
    
    def _pobierz_date_waznosci(self) -> datetime:
        """
        Pobiera datę ważności od użytkownika.
        
        Returns:
            datetime: Data ważności
        """
        while True:
            try:
                data_str = input("\nPodaj datę ważności (YYYY-MM-DD): ").strip()
                data = datetime.strptime(data_str, "%Y-%m-%d")
                
                if data.date() < datetime.now().date():
                    print("⚠️ Uwaga: Podana data jest z przeszłości!")
                    potwierdz = input("Czy na pewno chcesz kontynuować? (t/n): ")
                    if potwierdz.lower() != 't':
                        continue
                
                return data
            except ValueError:
                print("❌ Błędny format daty! Użyj formatu YYYY-MM-DD")
    
    def _pobierz_cene(self) -> Optional[float]:
        """
        Pobiera cenę produktu od użytkownika.
        
        Returns:
            Optional[float]: Cena produktu lub None
        """
        while True:
            cena_str = input("\n💰 Podaj cenę (opcjonalnie, Enter aby pominąć): ").strip()
            if not cena_str:
                return None
            try:
                cena = float(cena_str.replace(',', '.'))
                if cena < 0:
                    print("❌ Cena nie może być ujemna!")
                    continue
                return cena
            except ValueError:
                print("❌ Nieprawidłowy format ceny!")
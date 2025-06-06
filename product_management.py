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
                print(f"📦 Przeniesiono paragon do archiwum: {os.path.basename(archive_file)}")
                
                return True
            else:
                print("❌ Nie zaimportowano żadnych produktów")
                return False
            
        except Exception as e:
            print(f"❌ Błąd podczas importu paragonu: {e}")
            return False
    
    def szybkie_zarzadzanie_produktami(self) -> bool:
        """
        Umożliwia szybkie zarządzanie produktami (oznaczanie jako zużyte/usuwanie).
        
        Returns:
            bool: True jeśli operacja się powiodła, False w przeciwnym razie
        """
        try:
            produkty = self.storage_manager.wczytaj_produkty()
            produkty_aktywne = [p for p in produkty if not p.zuzyty]
            
            if not produkty_aktywne:
                print("📦 Brak aktywnych produktów do zarządzania")
                return False
            
            # Sortuj według daty ważności
            produkty_aktywne.sort(key=lambda x: x.data_waznosci)
            
            print("\n📋 Lista produktów do zarządzania:")
            for i, p in enumerate(produkty_aktywne, 1):
                dni_do_wygasniecia = (p.data_waznosci - datetime.now()).days
                print(f"{i}. {p.nazwa} ({p.kategoria}) - {dni_do_wygasniecia} dni do wygaśnięcia")
            
            print("\n0. Wróć")
            
            try:
                wybor = input("\nWybierz produkt do zarządzania (0-{len(produkty_aktywne)}): ")
                
                if wybor == "0":
                    return False
                
                idx = int(wybor) - 1
                if 0 <= idx < len(produkty_aktywne):
                    return self._zarzadzaj_produktem(produkty_aktywne[idx], produkty)
                else:
                    print("❌ Nieprawidłowy wybór")
                    return False
                    
            except ValueError:
                print("❌ Nieprawidłowy wybór")
                return False
            
        except Exception as e:
            print(f"❌ Błąd podczas zarządzania produktami: {e}")
            return False
    
    def _zarzadzaj_produktem(self, produkt: Produkt, wszystkie_produkty: List[Produkt]) -> bool:
        """
        Zarządza pojedynczym produktem.
        
        Args:
            produkt: Produkt do zarządzania
            wszystkie_produkty: Lista wszystkich produktów
            
        Returns:
            bool: True jeśli operacja się powiodła
        """
        print(f"\n📦 Zarządzanie produktem: {produkt.nazwa}")
        print("1. Oznacz jako zużyty")
        print("2. Usuń produkt")
        print("0. Wróć")
        
        try:
            wybor = input("\nWybierz operację (0-2): ")
            
            if wybor == "0":
                return False
            elif wybor == "1":
                produkt.zuzyty = True
                produkt.data_zuzycia = datetime.now()
                if self.storage_manager.zapisz_produkty(wszystkie_produkty):
                    print(f"✅ Oznaczono jako zużyty: {produkt.nazwa}")
                    return True
                else:
                    print("❌ Błąd podczas zapisywania zmian")
                    return False
            elif wybor == "2":
                potwierdz = input(f"Czy na pewno chcesz usunąć {produkt.nazwa}? (t/n): ").lower()
                if potwierdz == 't':
                    wszystkie_produkty.remove(produkt)
                    if self.storage_manager.zapisz_produkty(wszystkie_produkty):
                        print(f"✅ Usunięto produkt: {produkt.nazwa}")
                        return True
                    else:
                        print("❌ Błąd podczas zapisywania zmian")
                        return False
                return False
            else:
                print("❌ Nieprawidłowy wybór")
                return False
                
        except Exception as e:
            print(f"❌ Błąd podczas zarządzania produktem: {e}")
            return False
    
    def _wybierz_kategorie_reczne(self) -> str:
        """
        Umożliwia ręczny wybór kategorii produktu.
        
        Returns:
            str: Wybrana kategoria
        """
        print("\n📑 Dostępne kategorie:")
        for i, kat in enumerate(KATEGORIE, 1):
            print(f"{i}. {kat}")
        
        while True:
            try:
                wybor = int(input("\nWybierz kategorię (1-{len(KATEGORIE)}): "))
                if 1 <= wybor <= len(KATEGORIE):
                    return KATEGORIE[wybor - 1]
                else:
                    print("❌ Nieprawidłowy wybór")
            except ValueError:
                print("❌ Nieprawidłowy wybór")
    
    def _pobierz_date_waznosci(self) -> datetime:
        """
        Umożliwia ręczne wprowadzenie daty ważności.
        
        Returns:
            datetime: Data ważności
        """
        while True:
            try:
                data_str = input("\n🗓️ Podaj datę ważności (YYYY-MM-DD): ").strip()
                data = datetime.strptime(data_str, "%Y-%m-%d")
                
                # Sprawdź czy data nie jest z przeszłości
                if data.date() < datetime.now().date():
                    print("⚠️ Uwaga: Podana data jest z przeszłości!")
                    potwierdz = input("Czy na pewno chcesz kontynuować? (t/n): ").lower()
                    if potwierdz == 't':
                        return data
                else:
                    return data
                    
            except ValueError:
                print("❌ Błędny format daty. Użyj formatu YYYY-MM-DD")
    
    def _pobierz_cene(self) -> Optional[float]:
        """
        Umożliwia wprowadzenie ceny produktu (opcjonalnie).
        
        Returns:
            Optional[float]: Cena produktu lub None
        """
        cena_str = input("\n💰 Podaj cenę (Enter=pomiń): ").strip()
        if not cena_str:
            return None
            
        try:
            cena = float(cena_str.replace(',', '.'))
            if cena < 0:
                print("❌ Cena nie może być ujemna!")
                return None
            return cena
        except ValueError:
            print("❌ Błędny format ceny!")
            return None 
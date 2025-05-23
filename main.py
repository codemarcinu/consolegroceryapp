from typing import List, Dict, Any
from datetime import datetime, timedelta
import os
import glob
import json
import shutil
import cv2
import numpy as np
from pdf2image import convert_from_path

from models import Produkt
from config import KONFIGURACJA
from storage_manager import StorageManager
from product_management import ProductManager
from ocr_processor import ParagonProcessor
from llm_integration import OllamaClient
from ui_display import UIDisplay

class AsystentZakupow:
    """
    Główna klasa aplikacji zarządzająca wszystkimi komponentami.
    """
    
    def __init__(self):
        """
        Inicjalizuje główne komponenty aplikacji.
        """
        self.storage_manager = StorageManager()
        self.product_manager = ProductManager(self.storage_manager)
        self.paragon_processor = ParagonProcessor()
        self.llm_client = OllamaClient()
        self.ui = UIDisplay()
    
    def uruchom(self) -> None:
        """
        Uruchamia główną pętlę aplikacji.
        """
        # Sprawdź produkty wygasające przy starcie
        self._sprawdz_wygasajace_produkty()
        
        while True:
            self.ui.wyswietl_menu()
            wybor = self.ui.pobierz_wybor_menu()
            
            if wybor == "1":
                self._dodaj_szybki_produkt()
            elif wybor == "2":
                self._przetworz_paragony()
            elif wybor == "3":
                self._importuj_paragony()
            elif wybor == "4":
                self._przegladaj_spizarnie()
            elif wybor == "5":
                self._zarzadzaj_produktami()
            elif wybor == "6":
                self._sugeruj_przepisy()
            elif wybor == "7":
                self._pokaz_statystyki()
            elif wybor == "8":
                self.ui.wyswietl_komunikat("🚧 Funkcja w trakcie rozwoju!", "ostrzezenie")
            elif wybor == "9":
                self.ui.wyswietl_komunikat("👋 Do widzenia!", "sukces")
                break
    
    def _sprawdz_wygasajace_produkty(self) -> None:
        """
        Sprawdza produkty wygasające dzisiaj i jutro przy starcie aplikacji.
        """
        produkty = self.storage_manager.wczytaj_produkty()
        niezuzyty = [p for p in produkty if not p.zuzyty]
        
        dzisiaj = datetime.now().date()
        jutro = dzisiaj + timedelta(days=1)
        
        wygasaja_dzisiaj = []
        wygasaja_jutro = []
        
        for produkt in niezuzyty:
            data_produktu = produkt.data_waznosci.date()
            if data_produktu <= dzisiaj:
                wygasaja_dzisiaj.append(produkt)
            elif data_produktu == jutro:
                wygasaja_jutro.append(produkt)
        
        if wygasaja_dzisiaj or wygasaja_jutro:
            print("\n" + "=" * 50)
            print("⚠️  PRODUKTY WYMAGAJĄCE UWAGI!")
            print("=" * 50)
            
            if wygasaja_dzisiaj:
                print("\n🔴 WYGASAJĄ DZISIAJ:")
                for p in wygasaja_dzisiaj:
                    print(f"   • {p.nazwa} ({p.kategoria})")
            
            if wygasaja_jutro:
                print("\n🟡 WYGASAJĄ JUTRO:")
                for p in wygasaja_jutro:
                    print(f"   • {p.nazwa} ({p.kategoria})")
            
            print("=" * 50)
    
    def _dodaj_szybki_produkt(self) -> None:
        """
        Obsługuje dodawanie pojedynczego produktu.
        """
        if self.product_manager.dodaj_szybki_produkt(KONFIGURACJA["llm"]):
            self.ui.wyswietl_komunikat("✅ Produkt dodany pomyślnie!", "sukces")
        else:
            self.ui.wyswietl_komunikat("❌ Nie udało się dodać produktu!", "blad")
    
    def _przetworz_paragony(self) -> None:
        """
        Obsługuje przetwarzanie paragonów z obrazów.
        """
        print("\n🔄 Rozpoczynam przetwarzanie paragonów...")
        
        # Znajdź wszystkie pliki obrazów w folderze paragony/nowe
        pliki = []
        for rozszerzenie in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.pdf']:
            pliki.extend(glob.glob(f"paragony/nowe/*{rozszerzenie}"))
        
        if not pliki:
            print("❌ Nie znaleziono żadnych paragonów do przetworzenia!")
            return
        
        print(f"📸 Znaleziono {len(pliki)} paragonów do przetworzenia\n")
        
        przetworzone = 0
        bledy = 0
        
        for i, plik in enumerate(pliki, 1):
            print(f"\n🔍 Przetwarzam: {os.path.basename(plik)} ({i}/{len(pliki)})")
            
            try:
                # Konwertuj PDF do obrazu jeśli to PDF
                if plik.lower().endswith('.pdf'):
                    print("📄 Konwertuję PDF do obrazu...")
                    try:
                        # Konwertuj PDF do obrazu
                        obrazy = convert_from_path(plik)
                        if not obrazy:
                            print(f"❌ Nie udało się przekonwertować PDF '{plik}'")
                            bledy += 1
                            continue
                        
                        # Zapisz pierwszy obraz tymczasowo
                        temp_image = "temp_image.png"
                        obrazy[0].save(temp_image, "PNG")
                        
                        # Wczytaj obraz przez OpenCV
                        obraz = cv2.imread(temp_image)
                        
                        # Usuń tymczasowy plik
                        os.remove(temp_image)
                        
                        if obraz is None:
                            print(f"❌ Nie udało się wczytać przekonwertowanego obrazu")
                            bledy += 1
                            continue
                        
                    except Exception as e:
                        print(f"❌ Błąd podczas konwersji PDF '{plik}': {str(e)}")
                        bledy += 1
                        continue
                else:
                    obraz = cv2.imread(plik)
                    if obraz is None:
                        print(f"❌ Nie udało się odczytać obrazu '{plik}'")
                        bledy += 1
                        continue
                
                # Rozpoznaj tekst
                print("🔍 Rozpoznaję tekst...")
                tekst = self.paragon_processor.rozpoznaj_tekst(obraz)
                if not tekst:
                    print("❌ Nie udało się rozpoznać tekstu!")
                    bledy += 1
                    continue
                
                print("✅ Tekst rozpoznany, parsowanie przez AI...")
                # Parsuj tekst przez AI
                produkty = self.paragon_processor.parsuj_paragon_ai(tekst, KONFIGURACJA["llm"])
                if not produkty:
                    print("❌ AI nie znalazło produktów")
                    bledy += 1
                    continue
                
                # Zapisz przetworzone produkty
                nazwa_pliku = os.path.splitext(os.path.basename(plik))[0]
                sciezka_wyjsciowa = f"paragony/przetworzone/{nazwa_pliku}.json"
                
                # Upewnij się, że folder istnieje
                os.makedirs("paragony/przetworzone", exist_ok=True)
                
                with open(sciezka_wyjsciowa, 'w', encoding='utf-8') as f:
                    json.dump(produkty, f, ensure_ascii=False, indent=2)
                
                print(f"✅ Zapisano {len(produkty)} produktów do {sciezka_wyjsciowa}")
                przetworzone += 1
                
                # Przenieś przetworzony plik do archiwum
                archiwum = f"paragony/archiwum/{os.path.basename(plik)}"
                os.makedirs("paragony/archiwum", exist_ok=True)
                shutil.move(plik, archiwum)
                print(f"📦 Przeniesiono do archiwum: {archiwum}")
                
            except Exception as e:
                print(f"❌ Błąd podczas przetwarzania '{plik}': {str(e)}")
                bledy += 1
                continue
        
        print("\n📊 PODSUMOWANIE:")
        print(f"✅ Przetworzono: {przetworzone}")
        print(f"❌ Błędy: {bledy}")
        
        if bledy > 0:
            print(f"\n⚠️ ⚠️ Wystąpiło {bledy} błędów podczas przetwarzania!")
    
    def _importuj_paragony(self) -> None:
        """
        Obsługuje import przetworzonych paragonów do spiżarni.
        """
        if self.product_manager.importuj_przetworzone_paragony(KONFIGURACJA["llm"]):
            self.ui.wyswietl_komunikat("✅ Paragony zaimportowane pomyślnie!", "sukces")
        else:
            self.ui.wyswietl_komunikat("❌ Nie udało się zaimportować paragonów!", "blad")
    
    def _przegladaj_spizarnie(self) -> None:
        """
        Obsługuje przeglądanie zawartości spiżarni.
        """
        produkty = self.storage_manager.wczytaj_produkty()
        produkty_aktywne = [p for p in produkty if not p.zuzyty]
        
        if produkty_aktywne:
            # Sortuj według daty ważności
            produkty_aktywne.sort(key=lambda x: x.data_waznosci)
            self.ui.wyswietl_produkty(produkty_aktywne)
        else:
            self.ui.wyswietl_komunikat("📦 Spiżarnia jest pusta!", "info")
    
    def _zarzadzaj_produktami(self) -> None:
        """
        Obsługuje zarządzanie produktami (oznaczanie jako zużyte/usuwanie).
        """
        if self.product_manager.szybkie_zarzadzanie_produktami():
            self.ui.wyswietl_komunikat("✅ Operacja wykonana pomyślnie!", "sukces")
        # Nie wyświetlamy błędu jeśli użytkownik anulował operację
    
    def _sugeruj_przepisy(self) -> None:
        """
        Obsługuje generowanie sugestii przepisów na podstawie dostępnych produktów.
        """
        if not KONFIGURACJA["llm"]["enabled"]:
            self.ui.wyswietl_komunikat("⚠️ LLM jest wyłączone. Włącz go w konfiguracji aby używać sugestii przepisów.", "ostrzezenie")
            return
        
        produkty = self.storage_manager.wczytaj_produkty()
        produkty_aktywne = [p for p in produkty if not p.zuzyty]
        
        if not produkty_aktywne:
            self.ui.wyswietl_komunikat("❌ Brak produktów do sugestii przepisów!", "ostrzezenie")
            return
        
        # Produkty bliskie terminu (priorytet)
        bliskie_terminu = [p for p in produkty_aktywne 
                          if (p.data_waznosci - datetime.now()).days <= 3]
        
        # Wybierz max 8 produktów dla lepszej wydajności LLM
        skladniki = [p.nazwa for p in produkty_aktywne[:8]]
        priorytetowe = [p.nazwa for p in bliskie_terminu[:4]]
        
        print("\n🍳 Generuję sugestie przepisów...")
        print("🤖 AI analizuje dostępne składniki...")
        
        # Przygotuj prompt dla LLM
        prompt = f"""Na podstawie poniższych dostępnych składników, zaproponuj 3 proste i smaczne przepisy:

DOSTĘPNE SKŁADNIKI:
{', '.join(skladniki)}

SKŁADNIKI PRIORYTETOWE (kończą się za 3 dni lub wcześniej):
{', '.join(priorytetowe) if priorytetowe else 'Brak'}

WYMAGANIA:
- Przepisy mają być proste do wykonania
- Czas przygotowania maksymalnie 30 minut
- Użyj jak najwięcej dostępnych składników
- Priorytetowo użyj składniki kończące się terminów
- Każdy przepis powinien zawierać: nazwę, składniki, sposób przygotowania

FORMAT ODPOWIEDZI:
1. [NAZWA PRZEPISU]
Składniki: [lista składników]
Przygotowanie: [krótki opis sposób przygotowania]

2. [NAZWA PRZEPISU]
Składniki: [lista składników]  
Przygotowanie: [krótki opis sposób przygotowania]

3. [NAZWA PRZEPISU]
Składniki: [lista składników]
Przygotowanie: [krótki opis sposób przygotowania]"""
        
        system_prompt = """Jesteś doświadczonym kucharzem specjalizującym się w prostych, smacznych przepisach z dostępnych składników. 
Koncentrujesz się na wykorzystaniu składników, które mogą się zepsuć oraz tworzeniu praktycznych, łatwych do wykonania posiłków."""
        
        # Pobierz sugestie od LLM
        try:
            odpowiedz = self.llm_client.zapytaj_llm(
                prompt, 
                system_prompt,
                max_tokens=800,
                temperatura=0.7
            )
            
            if odpowiedz and not odpowiedz.startswith("Błąd"):
                print("\n" + "=" * 60)
                print("🍳 SUGESTIE PRZEPISÓW NA PODSTAWIE TWOJEJ SPIŻARNI")
                print("=" * 60)
                print(odpowiedz)
                print("=" * 60)
                
                # Opcja zapisu do pliku
                zapisz = input("\n💾 Zapisać przepisy do pliku? (t/n): ")
                if zapisz.lower() == 't':
                    try:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        nazwa_pliku = f"przepisy_{timestamp}.txt"
                        with open(nazwa_pliku, 'w', encoding='utf-8') as f:
                            f.write("SUGESTIE PRZEPISÓW - ASYSTENT SPIŻARNI\n")
                            f.write("=" * 50 + "\n")
                            f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                            f.write(f"Dostępne składniki: {', '.join(skladniki)}\n")
                            if priorytetowe:
                                f.write(f"Składniki priorytetowe: {', '.join(priorytetowe)}\n")
                            f.write("\n" + odpowiedz)
                        self.ui.wyswietl_komunikat(f"✅ Przepisy zapisane do pliku: {nazwa_pliku}", "sukces")
                    except Exception as e:
                        self.ui.wyswietl_komunikat(f"❌ Błąd podczas zapisywania: {e}", "blad")
            else:
                self.ui.wyswietl_komunikat(f"❌ Błąd podczas generowania przepisów: {odpowiedz}", "blad")
                
        except Exception as e:
            self.ui.wyswietl_komunikat(f"❌ Błąd podczas generowania przepisów: {e}", "blad")
    
    def _pokaz_statystyki(self) -> None:
        """
        Wyświetla statystyki spiżarni.
        """
        produkty = self.storage_manager.wczytaj_produkty()
        produkty_aktywne = [p for p in produkty if not p.zuzyty]
        
        if not produkty_aktywne:
            self.ui.wyswietl_komunikat("📦 Spiżarnia jest pusta!", "info")
            return
        
        # Statystyki podstawowe
        liczba_produktow = len(produkty_aktywne)
        wartosc_calkowita = sum(p.cena for p in produkty_aktywne if p.cena)
        
        # Statystyki kategorii
        kategorie = {}
        for p in produkty_aktywne:
            kategorie[p.kategoria] = kategorie.get(p.kategoria, 0) + 1
        
        # Produkty wygasające
        dzisiaj = datetime.now().date()
        wygasaja_wkrotce = [p for p in produkty_aktywne 
                           if (p.data_waznosci.date() - dzisiaj).days <= 3]
        
        print("\n" + "=" * 50)
        print("📊 STATYSTYKI SPIŻARNI")
        print("=" * 50)
        
        print(f"\n📦 Liczba produktów: {liczba_produktow}")
        if wartosc_calkowita > 0:
            print(f"💰 Wartość całkowita: {wartosc_calkowita:.2f} zł")
        
        print("\n📑 Produkty według kategorii:")
        for kat, liczba in sorted(kategorie.items()):
            print(f"   • {kat}: {liczba}")
        
        if wygasaja_wkrotce:
            print("\n⚠️ Produkty wygasające w ciągu 3 dni:")
            for p in wygasaja_wkrotce:
                dni_do_wygasniecia = (p.data_waznosci.date() - dzisiaj).days
                print(f"   • {p.nazwa} ({p.kategoria}) - {dni_do_wygasniecia} dni")
        
        print("=" * 50)

if __name__ == "__main__":
    # Upewnij się, że wszystkie wymagane katalogi istnieją
    for sciezka in [
        KONFIGURACJA["paths"]["paragony_nowe"],
        KONFIGURACJA["paths"]["paragony_przetworzone"],
        KONFIGURACJA["paths"]["paragony_bledy"],
        KONFIGURACJA["paths"]["dane_json_folder"],
        KONFIGURACJA["paths"]["archiwum_json"]
    ]:
        os.makedirs(sciezka, exist_ok=True)
    
    # Uruchom aplikację
    app = AsystentZakupow()
    app.uruchom() 
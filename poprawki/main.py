from typing import List, Dict, Any
from datetime import datetime, timedelta
import os

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
        self.ui.wyswietl_komunikat("🔄 Rozpoczynam przetwarzanie paragonów...", "info")
        przetworzone, bledy = self.paragon_processor.przetworz_wszystkie_paragony()
        
        if przetworzone > 0:
            self.ui.wyswietl_komunikat(
                f"✅ Przetworzono {przetworzone} paragonów!",
                "sukces"
            )
        if bledy > 0:
            self.ui.wyswietl_komunikat(
                f"⚠️ Wystąpiło {bledy} błędów podczas przetwarzania!",
                "ostrzezenie"
            )
        if przetworzone == 0 and bledy == 0:
            self.ui.wyswietl_komunikat("📁 Brak nowych paragonów do przetworzenia", "info")
    
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
            self.ui.wyswietl_komunikat(f"❌ Błąd podczas komunikacji z LLM: {e}", "blad")
    
    def _pokaz_statystyki(self) -> None:
        """
        Obsługuje wyświetlanie statystyk spiżarni.
        """
        produkty = self.storage_manager.wczytaj_produkty()
        self.ui.wyswietl_statystyki(produkty)

if __name__ == "__main__":
    print("🏠 Asystent Zakupów i Spiżarni v2")
    print("=" * 40)
    
    # Upewnij się, że wszystkie wymagane katalogi istnieją
    print("📁 Tworzenie wymaganych katalogów...")
    for sciezka in [
        KONFIGURACJA["paths"]["paragony_nowe"],
        KONFIGURACJA["paths"]["paragony_przetworzone"], 
        KONFIGURACJA["paths"]["paragony_bledy"],
        KONFIGURACJA["paths"]["dane_json_folder"],
        KONFIGURACJA["paths"]["archiwum_json"]
    ]:
        os.makedirs(sciezka, exist_ok=True)
    
    print("✅ Inicjalizacja zakończona")
    
    # Uruchom aplikację
    try:
        app = AsystentZakupow()
        app.uruchom()
    except KeyboardInterrupt:
        print("\n\n👋 Aplikacja przerwana przez użytkownika. Do widzenia!")
    except Exception as e:
        print(f"\n❌ Nieoczekiwany błąd aplikacji: {e}")
        print("Sprawdź konfigurację i spróbuj ponownie.")
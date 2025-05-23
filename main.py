from typing import List, Dict, Any
from datetime import datetime
import os

from models import Produkt
from config import KONFIGURACJA
from storage_manager import StorageManager
from product_management import ProductManager
from ocr_processor import ParagonProcessor
from llm_integration import OllamaClient, parsuj_paragon_ai, sugeruj_kategorie, sugeruj_date_waznosci
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
                self.ui.wyswietl_komunikat("Funkcja w trakcie rozwoju!", "ostrzezenie")
            elif wybor == "9":
                self.ui.wyswietl_komunikat("Do widzenia!", "sukces")
                break
    
    def _dodaj_szybki_produkt(self) -> None:
        """
        Obsługuje dodawanie pojedynczego produktu.
        """
        if self.product_manager.dodaj_szybki_produkt(KONFIGURACJA["llm"]):
            self.ui.wyswietl_komunikat("Produkt dodany pomyślnie!", "sukces")
        else:
            self.ui.wyswietl_komunikat("Nie udało się dodać produktu!", "blad")
    
    def _przetworz_paragony(self) -> None:
        """
        Obsługuje przetwarzanie paragonów z obrazów.
        """
        self.ui.wyswietl_komunikat("Przetwarzanie paragonów...", "info")
        przetworzone, bledy = self.paragon_processor.przetworz_wszystkie_paragony()
        
        if przetworzone > 0:
            self.ui.wyswietl_komunikat(
                f"Przetworzono {przetworzone} paragonów!",
                "sukces"
            )
        if bledy > 0:
            self.ui.wyswietl_komunikat(
                f"Wystąpiło {bledy} błędów podczas przetwarzania!",
                "ostrzezenie"
            )
    
    def _importuj_paragony(self) -> None:
        """
        Obsługuje import przetworzonych paragonów do spiżarni.
        """
        if self.product_manager.importuj_przetworzone_paragony(KONFIGURACJA["llm"]):
            self.ui.wyswietl_komunikat("Paragony zaimportowane pomyślnie!", "sukces")
        else:
            self.ui.wyswietl_komunikat("Nie udało się zaimportować paragonów!", "blad")
    
    def _przegladaj_spizarnie(self) -> None:
        """
        Obsługuje przeglądanie zawartości spiżarni.
        """
        produkty = self.storage_manager.wczytaj_produkty()
        self.ui.wyswietl_produkty(produkty)
    
    def _zarzadzaj_produktami(self) -> None:
        """
        Obsługuje zarządzanie produktami (oznaczanie jako zużyte/usuwanie).
        """
        if self.product_manager.szybkie_zarzadzanie_produktami():
            self.ui.wyswietl_komunikat("Operacja wykonana pomyślnie!", "sukces")
        else:
            self.ui.wyswietl_komunikat("Nie udało się wykonać operacji!", "blad")
    
    def _sugeruj_przepisy(self) -> None:
        """
        Obsługuje generowanie sugestii przepisów na podstawie dostępnych produktów.
        """
        produkty = self.storage_manager.wczytaj_produkty()
        produkty_aktywne = [p for p in produkty if not p.zuzyty]
        
        if not produkty_aktywne:
            self.ui.wyswietl_komunikat("Brak produktów do sugestii przepisów!", "ostrzezenie")
            return
        
        # Przygotuj prompt dla LLM
        prompt = "Na podstawie poniższych produktów, zaproponuj 3 przepisy:\n\n"
        for p in produkty_aktywne:
            prompt += f"- {p.nazwa} ({p.kategoria})\n"
        
        prompt += "\nDla każdego przepisu podaj:\n"
        prompt += "1. Nazwę przepisu\n"
        prompt += "2. Listę składników\n"
        prompt += "3. Sposób przygotowania\n"
        
        # Pobierz sugestie od LLM
        odpowiedz = self.llm_client.zapytaj_llm(prompt)
        
        # Przetwórz odpowiedź na listę przepisów
        sugestie = []
        try:
            # TODO: Implementacja parsowania odpowiedzi LLM na strukturę przepisów
            # Na razie wyświetlamy surową odpowiedź
            self.ui.wyswietl_komunikat(odpowiedz, "info")
        except Exception as e:
            self.ui.wyswietl_komunikat(f"Błąd podczas przetwarzania sugestii: {str(e)}", "blad")
    
    def _pokaz_statystyki(self) -> None:
        """
        Obsługuje wyświetlanie statystyk spiżarni.
        """
        produkty = self.storage_manager.wczytaj_produkty()
        self.ui.wyswietl_statystyki(produkty)

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
import json
import os
from typing import List, Optional
from datetime import datetime
from models import Produkt
from config import KONFIGURACJA

class StorageManager:
    """
    Klasa zarządzająca przechowywaniem i wczytywaniem danych aplikacji.
    """
    
    def __init__(self, sciezka_pliku: Optional[str] = None):
        """
        Inicjalizuje menedżer przechowywania danych.
        
        Args:
            sciezka_pliku: Opcjonalna ścieżka do pliku JSON z produktami
        """
        self.sciezka_pliku = sciezka_pliku or KONFIGURACJA["paths"]["produkty_json_file"]
        self._zapewnij_istnienie_pliku()
    
    def _zapewnij_istnienie_pliku(self) -> None:
        """
        Tworzy plik JSON z produktami, jeśli nie istnieje.
        """
        if not os.path.exists(self.sciezka_pliku):
            os.makedirs(os.path.dirname(self.sciezka_pliku), exist_ok=True)
            with open(self.sciezka_pliku, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False)
    
    def wczytaj_produkty(self) -> List[Produkt]:
        """
        Wczytuje listę produktów z pliku JSON.
        
        Returns:
            List[Produkt]: Lista obiektów Produkt
        """
        try:
            with open(self.sciezka_pliku, 'r', encoding='utf-8') as f:
                dane = json.load(f)
            return [Produkt.from_dict(p) for p in dane]
        except Exception as e:
            print(f"Błąd podczas wczytywania produktów: {e}")
            return []
    
    def zapisz_produkty(self, produkty: List[Produkt]) -> bool:
        """
        Zapisuje listę produktów do pliku JSON.
        
        Args:
            produkty: Lista obiektów Produkt do zapisania
            
        Returns:
            bool: True jeśli zapis się powiódł, False w przeciwnym razie
        """
        try:
            dane = [p.to_dict() for p in produkty]
            with open(self.sciezka_pliku, 'w', encoding='utf-8') as f:
                json.dump(dane, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Błąd podczas zapisywania produktów: {e}")
            return False
    
    def dodaj_produkt(self, produkt: Produkt) -> bool:
        """
        Dodaje pojedynczy produkt do pliku JSON.
        
        Args:
            produkt: Obiekt Produkt do dodania
            
        Returns:
            bool: True jeśli dodanie się powiodło, False w przeciwnym razie
        """
        try:
            produkty = self.wczytaj_produkty()
            produkty.append(produkt)
            return self.zapisz_produkty(produkty)
        except Exception as e:
            print(f"Błąd podczas dodawania produktu: {e}")
            return False
    
    def usun_produkt(self, indeks: int) -> bool:
        """
        Usuwa produkt o podanym indeksie z pliku JSON.
        
        Args:
            indeks: Indeks produktu do usunięcia
            
        Returns:
            bool: True jeśli usunięcie się powiodło, False w przeciwnym razie
        """
        try:
            produkty = self.wczytaj_produkty()
            if 0 <= indeks < len(produkty):
                produkty.pop(indeks)
                return self.zapisz_produkty(produkty)
            return False
        except Exception as e:
            print(f"Błąd podczas usuwania produktu: {e}")
            return False
    
    def oznacz_jako_zuzyty(self, indeks: int) -> bool:
        """
        Oznacza produkt o podanym indeksie jako zużyty.
        
        Args:
            indeks: Indeks produktu do oznaczenia
            
        Returns:
            bool: True jeśli operacja się powiodła, False w przeciwnym razie
        """
        try:
            produkty = self.wczytaj_produkty()
            if 0 <= indeks < len(produkty):
                produkty[indeks].zuzyty = True
                return self.zapisz_produkty(produkty)
            return False
        except Exception as e:
            print(f"Błąd podczas oznaczania produktu jako zużytego: {e}")
            return False
    
    def zapisz_przetworzony_paragon(self, dane_paragonu: dict) -> bool:
        """
        Zapisuje dane przetworzonego paragonu do pliku JSON.
        
        Args:
            dane_paragonu: Słownik z danymi paragonu
            
        Returns:
            bool: True jeśli zapis się powiódł, False w przeciwnym razie
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sciezka_pliku = os.path.join(
                KONFIGURACJA["paths"]["dane_json_folder"],
                f"paragon_{timestamp}.json"
            )
            with open(sciezka_pliku, 'w', encoding='utf-8') as f:
                json.dump(dane_paragonu, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Błąd podczas zapisywania przetworzonego paragonu: {e}")
            return False 
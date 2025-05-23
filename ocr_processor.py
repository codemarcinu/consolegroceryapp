import easyocr
import cv2
import numpy as np
import os
import shutil
from datetime import datetime
from typing import Optional, List
from config import KONFIGURACJA

class ParagonProcessor:
    """
    Klasa do przetwarzania obrazów paragonów.
    """
    
    def __init__(self):
        """
        Inicjalizuje procesor paragonów.
        """
        # Inicjalizacja EasyOCR z językiem polskim i angielskim
        self.reader = easyocr.Reader(['pl', 'en'], 
                                   gpu=KONFIGURACJA["ocr"]["gpu"])
        
        # Foldery do przechowywania paragonów
        self.folder_nowe = KONFIGURACJA["paths"]["paragony_nowe"]
        self.folder_przetworzone = KONFIGURACJA["paths"]["paragony_przetworzone"]
        self.folder_bledy = KONFIGURACJA["paths"]["paragony_bledy"]
        
        # Tworzenie folderów, jeśli nie istnieją
        for folder in [self.folder_nowe, self.folder_przetworzone, self.folder_bledy]:
            os.makedirs(folder, exist_ok=True)
    
    def przygotuj_obraz(self, sciezka_pliku: str) -> Optional[np.ndarray]:
        """
        Przygotowuje obraz paragonu do OCR.
        
        Args:
            sciezka_pliku: Ścieżka do pliku obrazu
            
        Returns:
            Optional[np.ndarray]: Przygotowany obraz lub None w przypadku błędu
        """
        try:
            img = cv2.imread(sciezka_pliku)
            if img is None:
                print(f"❌ Nie można wczytać obrazu: {sciezka_pliku}")
                return None
            
            # Konwersja do skali szarości
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Poprawa kontrastu (CLAHE)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced_contrast = clahe.apply(gray)
            
            # Adaptacyjna binaryzacja
            binary_img = cv2.adaptiveThreshold(
                enhanced_contrast, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            
            return binary_img
            
        except Exception as e:
            print(f"❌ Błąd podczas przygotowywania obrazu '{sciezka_pliku}': {e}")
            return None
    
    def rozpoznaj_tekst(self, sciezka_pliku: str) -> Optional[str]:
        """
        Rozpoznaje tekst z obrazu paragonu.
        
        Args:
            sciezka_pliku: Ścieżka do pliku obrazu
            
        Returns:
            Optional[str]: Rozpoznany tekst lub None w przypadku błędu
        """
        try:
            przygotowany_obraz = self.przygotuj_obraz(sciezka_pliku)
            if przygotowany_obraz is None:
                return None
            
            # OCR z EasyOCR
            results = self.reader.readtext(
                przygotowany_obraz,
                detail=0,
                paragraph=True,
                min_size=5
            )
            
            if not results:
                print(f"⚠️ EasyOCR nie znalazł tekstu w: {sciezka_pliku}")
                return None
            
            return '\n'.join(results)
            
        except Exception as e:
            print(f"❌ Błąd OCR dla pliku '{sciezka_pliku}': {e}")
            return None
    
    def przetworz_paragon(self, sciezka_pliku: str) -> bool:
        """
        Przetwarza pojedynczy paragon.
        
        Args:
            sciezka_pliku: Ścieżka do pliku obrazu
            
        Returns:
            bool: True jeśli przetwarzanie się powiodło, False w przeciwnym razie
        """
        try:
            # Rozpoznaj tekst
            tekst = self.rozpoznaj_tekst(sciezka_pliku)
            if not tekst:
                self._przenies_do_folderu(sciezka_pliku, self.folder_bledy)
                return False
            
            # Przenieś plik do folderu przetworzonych
            self._przenies_do_folderu(sciezka_pliku, self.folder_przetworzone)
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas przetwarzania paragonu '{sciezka_pliku}': {e}")
            self._przenies_do_folderu(sciezka_pliku, self.folder_bledy)
            return False
    
    def przetworz_wszystkie_paragony(self) -> tuple[int, int]:
        """
        Przetwarza wszystkie paragony z folderu nowych.
        
        Returns:
            tuple[int, int]: Liczba przetworzonych paragonów i liczba błędów
        """
        przetworzone = 0
        bledy = 0
        
        # Znajdź wszystkie pliki obrazów
        rozszerzenia = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        pliki = []
        for rozszerzenie in rozszerzenia:
            pliki.extend([
                os.path.join(self.folder_nowe, f)
                for f in os.listdir(self.folder_nowe)
                if f.lower().endswith(rozszerzenie)
            ])
        
        # Przetwórz każdy plik
        for plik in pliki:
            if self.przetworz_paragon(plik):
                przetworzone += 1
            else:
                bledy += 1
        
        return przetworzone, bledy
    
    def _przenies_do_folderu(self, sciezka_pliku: str, folder_docelowy: str) -> None:
        """
        Przenosi plik do wskazanego folderu.
        
        Args:
            sciezka_pliku: Ścieżka do pliku
            folder_docelowy: Folder docelowy
        """
        try:
            nazwa_pliku = os.path.basename(sciezka_pliku)
            sciezka_docelowa = os.path.join(folder_docelowy, nazwa_pliku)
            shutil.move(sciezka_pliku, sciezka_docelowa)
        except Exception as e:
            print(f"❌ Błąd podczas przenoszenia pliku '{sciezka_pliku}': {e}") 
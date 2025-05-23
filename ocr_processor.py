import easyocr
import cv2
import numpy as np
import os
import shutil
import json
import glob
from datetime import datetime
from typing import Optional, List, Tuple
from config import KONFIGURACJA
from llm_integration import parsuj_paragon_ai
from storage_manager import StorageManager
import tempfile
from pdf2image import convert_from_path

class ParagonProcessor:
    """
    Klasa do przetwarzania obrazów paragonów z pełną funkcjonalnością OCR + AI.
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
        
        # Menedżer przechowywania danych
        self.storage_manager = StorageManager()
        
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
            
            # Rozmazanie gaussowskie + wyostrzenie
            blurred = cv2.GaussianBlur(enhanced_contrast, (0,0), 1.0)
            sharpened = cv2.addWeighted(enhanced_contrast, 1.5, blurred, -0.5, 0)
            
            # Binaryzacja Otsu
            _, binary_img = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
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
            results = self.reader.readtext(przygotowany_obraz)
            
            if not results:
                print(f"⚠️ EasyOCR nie znalazł tekstu w: {sciezka_pliku}")
                return None
            
            # Wyciągnij tekst z wyników
            tekst_lines = []
            for (bbox, text, confidence) in results:
                if confidence > 0.3:  # Tylko tekst z dobrą pewnością
                    tekst_lines.append(text.strip())
            
            return '\n'.join(tekst_lines)
            
        except Exception as e:
            print(f"❌ Błąd OCR dla pliku '{sciezka_pliku}': {e}")
            return None
    
    def przetworz_paragon(self, sciezka_pliku: str) -> bool:
        """
        Przetwarza pojedynczy paragon: OCR + AI parsing + zapis JSON.
        
        Args:
            sciezka_pliku: Ścieżka do pliku obrazu
            
        Returns:
            bool: True jeśli przetwarzanie się powiodło, False w przeciwnym razie
        """
        nazwa_pliku = os.path.basename(sciezka_pliku)
        print(f"\n🔍 Przetwarzam: {nazwa_pliku}")
        
        try:
            # 1. Rozpoznaj tekst (OCR)
            tekst = self.rozpoznaj_tekst(sciezka_pliku)
            if not tekst:
                print("❌ Nie udało się rozpoznać tekstu")
                self._przenies_do_folderu(sciezka_pliku, self.folder_bledy)
                return False
            
            print("✅ Tekst rozpoznany, parsowanie przez AI...")
            
            # 2. Parsuj produkty przez AI
            produkty = parsuj_paragon_ai(tekst, KONFIGURACJA["llm"])
            
            if not produkty:
                print("❌ AI nie znalazło produktów")
                self._przenies_do_folderu(sciezka_pliku, self.folder_bledy)
                return False
            
            print(f"🛒 AI znalazło {len(produkty)} produktów:")
            for p in produkty:
                print(f"   • {p['nazwa']} - {p['cena']:.2f} zł")
            
            # 3. Zapisz produkty do JSON dla dalszego przetwarzania
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            paragon_data = {
                'plik_zrodlowy': nazwa_pliku,
                'data_przetworzenia': timestamp,
                'tekst_ocr': tekst,
                'produkty': produkty
            }
            
            # Zapisz do folderu data/
            json_filename = f"paragon_{timestamp}.json"
            json_path = os.path.join(KONFIGURACJA["paths"]["dane_json_folder"], json_filename)
            
            if self.storage_manager.zapisz_przetworzony_paragon(paragon_data):
                print(f"✅ Paragon przetworzony i zapisany jako {json_filename}")
                
                # 4. Przenieś obraz do folderu przetworzonych
                self._przenies_do_folderu(sciezka_pliku, self.folder_przetworzone)
                return True
            else:
                print("❌ Błąd podczas zapisywania danych paragonu")
                self._przenies_do_folderu(sciezka_pliku, self.folder_bledy)
                return False
            
        except Exception as e:
            print(f"❌ Błąd podczas przetwarzania paragonu '{nazwa_pliku}': {e}")
            self._przenies_do_folderu(sciezka_pliku, self.folder_bledy)
            return False
    
    def przetworz_wszystkie_paragony(self) -> Tuple[int, int]:
        """
        Przetwarza wszystkie paragony z folderu nowych.
        
        Returns:
            Tuple[int, int]: Liczba przetworzonych paragonów i liczba błędów
        """
        # Znajdź wszystkie pliki obrazów oraz PDF
        extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.pdf', '*.PDF']
        pliki_do_przetworzenia = []
        for ext in extensions:
            pliki_do_przetworzenia.extend(glob.glob(os.path.join(self.folder_nowe, ext)))
        if not pliki_do_przetworzenia:
            print("📁 Brak nowych paragonów do przetworzenia")
            return 0, 0
        print(f"📸 Znaleziono {len(pliki_do_przetworzenia)} paragonów do przetworzenia")
        przetworzono = 0
        bledy = 0
        for sciezka_pliku in pliki_do_przetworzenia:
            if sciezka_pliku.lower().endswith('.pdf'):
                # Konwertuj każdą stronę PDF na obraz i przetwarzaj
                try:
                    obrazy = convert_from_path(sciezka_pliku, dpi=300)
                    for idx, obraz in enumerate(obrazy):
                        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_img:
                            obraz.save(tmp_img.name, 'JPEG')
                            wynik = self.przetworz_paragon(tmp_img.name)
                            if wynik:
                                przetworzono += 1
                            else:
                                bledy += 1
                            os.unlink(tmp_img.name)
                    # Po przetworzeniu przenieś PDF do przetworzonych lub błędów (jeśli choć jedna strona się udała)
                    if przetworzono > 0:
                        self._przenies_do_folderu(sciezka_pliku, self.folder_przetworzone)
                    else:
                        self._przenies_do_folderu(sciezka_pliku, self.folder_bledy)
                except Exception as e:
                    print(f"❌ Błąd podczas konwersji PDF '{sciezka_pliku}': {e}")
                    self._przenies_do_folderu(sciezka_pliku, self.folder_bledy)
                    bledy += 1
            else:
                if self.przetworz_paragon(sciezka_pliku):
                    przetworzono += 1
                else:
                    bledy += 1
        print(f"\n📊 PODSUMOWANIE:")
        print(f"✅ Przetworzono: {przetworzono}")
        print(f"❌ Błędy: {bledy}")
        if przetworzono > 0:
            print(f"\n🔄 Użyj opcji 'Importuj przetworzone paragony' aby dodać produkty do spiżarni")
        return przetworzono, bledy
    
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
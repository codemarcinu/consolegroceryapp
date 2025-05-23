import os
import json
from typing import Dict, Any

# Kategorie produktów
KATEGORIE = [
    "Nabiał", "Mięso/Wędliny", "Ryby i owoce morza", "Mrożonki",
    "Warzywa", "Owoce", "Pieczywo", "Produkty Suche/Sypkie",
    "Słodycze i przekąski", "Napoje", "Dania gotowe", "Przyprawy i sosy",
    "Konserwy i przetwory", "Chemia domowa", "Kosmetyki", "Dla dzieci", "Inne"
]

# Domyślna konfiguracja
DEFAULT_CONFIG = {
    "llm": {
        "enabled": True,
        "model": "speakleash/bielik-1.5b-v3.0-instruct",
        "base_url": "http://localhost:11434",
        "timeout_seconds": 60,
        "max_tokens": 1024,
        "temperatura": 0.1,
        "auto_categorize": True,
        "auto_expiry_date": True
    },
    "ocr": {
        "gpu": False
    },
    "paths": {
        "paragony_nowe": "paragony/nowe/",
        "paragony_przetworzone": "paragony/przetworzone/",
        "paragony_bledy": "paragony/bledy/",
        "dane_json_folder": "data/",
        "produkty_json_file": "data/produkty.json",
        "config_json_file": "data/config.json",
        "archiwum_json": "data/archive/"
    },
    "interface": {
        "language": "pl",
        "colors_enabled": True,
        "table_format": "fancy_grid"
    },
    "notifications": {
        "expiry_warning_days_critical": 3,
        "expiry_warning_days_warning": 7
    }
}

def wczytaj_konfiguracje() -> Dict[str, Any]:
    """
    Wczytuje konfigurację z pliku JSON lub tworzy domyślną.
    
    Returns:
        Dict[str, Any]: Słownik z konfiguracją
    """
    config_path = DEFAULT_CONFIG["paths"]["config_json_file"]
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Błąd podczas wczytywania konfiguracji: {e}")
            print("Używam domyślnej konfiguracji.")
            return DEFAULT_CONFIG
    else:
        # Tworzenie domyślnej konfiguracji
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
            return DEFAULT_CONFIG
        except Exception as e:
            print(f"Błąd podczas tworzenia domyślnej konfiguracji: {e}")
            return DEFAULT_CONFIG

def zapisz_konfiguracje(konfiguracja: Dict[str, Any]) -> bool:
    """
    Zapisuje konfigurację do pliku JSON.
    
    Args:
        konfiguracja: Słownik z konfiguracją do zapisania
        
    Returns:
        bool: True jeśli zapis się powiódł, False w przeciwnym razie
    """
    config_path = konfiguracja["paths"]["config_json_file"]
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(konfiguracja, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Błąd podczas zapisywania konfiguracji: {e}")
        return False

# Wczytaj konfigurację przy imporcie modułu
KONFIGURACJA = wczytaj_konfiguracje() 
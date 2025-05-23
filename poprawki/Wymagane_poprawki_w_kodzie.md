# 🔧 Wymagane poprawki w kodzie

## 1. Natychmiastowe poprawki błędów

### `llm_integration.py` - Linia 69-75
```python
# ZAMIEŃ:
prompt = f"""Przypisz poniższy produkt do jednej z następujących kategorii:
{Nazwa_produktu}
Dostępne kategorie:
{Nazwa_produktu}

# NA:
from config import KATEGORIE
kategorie_str = "\n".join([f"{i+1}. {kat}" for i, kat in enumerate(KATEGORIE)])
prompt = f"""Przypisz poniższy produkt do jednej z następujących kategorii:
Produkt: {nazwa_produktu}
Dostępne kategorie:
{kategorie_str}
```

### `product_management.py` - Dodaj importy na początku
```python
import json
import os
import shutil
import glob
```

## 2. Zastąp pliki kompletne (w artifacts)

- **`ocr_processor.py`** → Kompletna implementacja OCR + AI
- **`product_management.py`** → Poprawiona wersja z import paragonów
- **`main.py`** → Pełna implementacja sugestii przepisów
- **`llm_integration.py`** → Poprawiona funkcja kategoryzacji

## 3. Dodatkowe usprawnienia

### Sprawdzanie produktów przy starcie
Dodane w `main.py` - funkcja `_sprawdz_wygasajace_produkty()`

### Lepsza obsługa błędów
- Walidacja dat z ostrzeżeniami
- Obsługa braku modułu fuzzywuzzy
- Graceful degradation bez LLM

### Zapisywanie przepisów do pliku
Dodana opcja w `_sugeruj_przepisy()`

## 4. Instrukcja wdrożenia poprawek

1. **Zastąp pliki** zawartością z artifacts
2. **Zainstaluj zależności**: `pip install -r requirements.txt`
3. **Uruchom Ollama**: `ollama serve`
4. **Testuj aplikację**: `python main.py`

## 5. Testy funkcjonalności

- [ ] Dodawanie produktów z AI sugestiami
- [ ] Przetwarzanie paragonów (OCR + AI)
- [ ] Import przetworzonych paragonów  
- [ ] Sugestie przepisów
- [ ] Zarządzanie produktami
- [ ] Statystyki i powiadomienia
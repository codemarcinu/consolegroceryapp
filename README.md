# Asystent Zakupów i Spiżarni v2

Aplikacja konsolowa do zarządzania domowymi zapasami spożywczymi, napisana w Pythonie.

## Funkcjonalności

- Szybkie dodawanie produktów do spiżarni
- Automatyczne przetwarzanie paragonów z obrazów (OCR + AI)
- Import przetworzonych paragonów do spiżarni
- Przeglądanie zawartości spiżarni
- Zarządzanie produktami (oznaczanie jako zużyte/usuwanie)
- Sugestie przepisów na podstawie dostępnych produktów (AI)
- Statystyki spiżarni

## Wymagania

- Python 3.8+
- Ollama (do obsługi modeli AI)
- Kamerka internetowa lub skaner (do skanowania paragonów)

## Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/twoje-repozytorium/asystent-zakupow.git
cd asystent-zakupow
```

2. Zainstaluj wymagane pakiety:
```bash
pip install -r requirements.txt
```

3. Upewnij się, że masz zainstalowane i uruchomione Ollama:
```bash
# Instalacja Ollama (Linux)
curl https://ollama.ai/install.sh | sh

# Uruchomienie Ollama
ollama serve
```

## Struktura projektu

```
asystent-zakupow/
├── data/
│   ├── archive/        # Archiwum produktów
│   └── produkty.json   # Baza danych produktów
├── paragony/
│   ├── nowe/          # Nowe paragony do przetworzenia
│   ├── przetworzone/  # Przetworzone paragony
│   └── bledy/         # Paragony z błędami
├── config.py          # Konfiguracja aplikacji
├── llm_integration.py # Integracja z Ollama
├── main.py           # Główny plik aplikacji
├── models.py         # Modele danych
├── ocr_processor.py  # Przetwarzanie paragonów
├── product_management.py # Zarządzanie produktami
├── storage_manager.py    # Zarządzanie danymi
├── ui_display.py     # Interfejs użytkownika
└── requirements.txt  # Zależności projektu
```

## Użycie

1. Uruchom aplikację:
```bash
python main.py
```

2. Wybierz opcję z menu:
   - 1: Dodaj produkt (szybko)
   - 2: Przetwórz paragony z obrazów (OCR + AI)
   - 3: Importuj przetworzone paragony do spiżarni
   - 4: Przeglądaj spiżarnię
   - 5: Zarządzaj produktami (zużyj/usuń)
   - 6: Sugestie przepisów (AI)
   - 7: Statystyki spiżarni
   - 8: Ustawienia (w trakcie rozwoju)
   - 9: Wyjście

## Przetwarzanie paragonów

1. Umieść zdjęcia paragonów **lub pliki PDF** w folderze `paragony/nowe/`
2. Wybierz opcję 2 z menu głównego
3. Aplikacja automatycznie przetworzy paragony (w tym PDF-y) i przeniesie je do odpowiednich folderów
4. Wybierz opcję 3, aby zaimportować przetworzone paragony do spiżarni

### Obsługa PDF
Aplikacja automatycznie konwertuje każdą stronę PDF na obraz i przetwarza ją jak zwykłe zdjęcie paragonu. Nie musisz już ręcznie konwertować PDF-ów na JPG.

## Konfiguracja

Konfiguracja aplikacji znajduje się w pliku `config.py`. Możesz dostosować:
- Ustawienia LLM (model, URL, timeout, itp.)
- Ustawienia OCR
- Ścieżki do folderów
- Ustawienia interfejsu
- Ustawienia powiadomień o terminach ważności

## Rozwój

Aplikacja jest w trakcie rozwoju. Planowane funkcje:
- Ustawienia aplikacji
- Eksport/import danych
- Integracja z innymi modelami AI
- Rozszerzenie funkcji sugestii przepisów

## Licencja

MIT License 
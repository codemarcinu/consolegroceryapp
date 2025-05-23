import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from config import KONFIGURACJA

class OllamaClient:
    """
    Klasa do komunikacji z modelem Ollama.
    """
    
    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None):
        """
        Inicjalizuje klienta Ollama.
        
        Args:
            model: Nazwa modelu (domyślnie z konfiguracji)
            base_url: URL serwera Ollama (domyślnie z konfiguracji)
        """
        self.model = model or KONFIGURACJA["llm"]["model"]
        self.base_url = base_url or KONFIGURACJA["llm"]["base_url"]
    
    def zapytaj_llm(self, prompt: str, system_prompt: str = "", 
                   max_tokens: Optional[int] = None,
                   temperatura: Optional[float] = None) -> str:
        """
        Wysyła zapytanie do modelu LLM.
        
        Args:
            prompt: Tekst zapytania
            system_prompt: Opcjonalny prompt systemowy
            max_tokens: Maksymalna liczba tokenów w odpowiedzi
            temperatura: Temperatura generowania (0.0-1.0)
            
        Returns:
            str: Odpowiedź modelu lub komunikat o błędzie
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperatura or KONFIGURACJA["llm"]["temperatura"],
                        "num_predict": max_tokens or KONFIGURACJA["llm"]["max_tokens"],
                        "top_p": 0.9
                    }
                },
                timeout=KONFIGURACJA["llm"]["timeout_seconds"]
            )
            
            if response.status_code == 200:
                return response.json()["response"].strip()
            else:
                return f"Błąd HTTP {response.status_code}: {response.text}"
                
        except requests.exceptions.Timeout:
            return "Błąd: Model Ollama nie odpowiedział w wyznaczonym czasie (timeout)."
        except requests.exceptions.RequestException as e:
            return f"Błąd połączenia z LLM Ollama: {e}"
        except Exception as e:
            return f"Nieoczekiwany błąd podczas komunikacji z LLM: {e}"

def parsuj_paragon_ai(tekst_paragonu: str, konfiguracja_llm: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Używa LLM do wyciągnięcia nazw produktów i ich cen z tekstu paragonu.
    
    Args:
        tekst_paragonu: Tekst paragonu do przetworzenia
        konfiguracja_llm: Konfiguracja LLM
        
    Returns:
        List[Dict[str, Any]]: Lista produktów z nazwami i cenami
    """
    if not tekst_paragonu or not tekst_paragonu.strip():
        return []

    system_prompt = """Jesteś zaawansowanym analitykiem specjalizującym się w ekstrakcji danych ze skanów polskich paragonów fiskalnych. Twoim głównym zadaniem jest identyfikacja i precyzyjne wyodrębnienie listy zakupionych produktów wraz z ich ostatecznymi cenami (po uwzględnieniu wszelkich rabatów przypisanych bezpośrednio do produktu)."""

    prompt = f"""Przeanalizuj poniższy tekst z paragonu i wyodrębnij z niego wyłącznie linie zawierające produkty oraz ich ceny końcowe.

Tekst paragonu:
--- POCZĄTEK TEKSTU PARAGONU ---
{tekst_paragonu}
--- KONIEC TEKSTU PARAGONU ---

Zasady ekstrakcji:
1. Format wyjściowy dla każdej pozycji: NAZWA_PRODUKTU|CENA_FINALNA
2. Cena końcowa: Skup się na wartości, która faktycznie została doliczona do sumy paragonu za tę pozycję.
3. Ilość i waga: Jeśli produkt jest sprzedawany na sztuki lub wagę, wyciągnij nazwę produktu i cenę końcową za wszystkie sztuki/wagę.
4. Rabaty: Jeśli rabat jest podany bezpośrednio przy produkcie, odejmij go od ceny produktu.
5. Ignoruj linie niebędące produktami: nagłówki, sumy, podatki, dane sklepu, NIP, adresy, programy lojalnościowe, informacje o płatności, daty/godziny (chyba że część nazwy produktu).

Zwróć tylko linie produktowe w podanym formacie, każda w nowej linii."""

    llm = OllamaClient(model=konfiguracja_llm.get('model'),
                      base_url=konfiguracja_llm.get('base_url'))
    
    odpowiedz_llm = llm.zapytaj_llm(prompt, system_prompt,
                                   max_tokens=konfiguracja_llm.get('max_tokens'),
                                   temperatura=konfiguracja_llm.get('temperatura'))

    produkty_wyekstrahowane = []
    if odpowiedz_llm and not odpowiedz_llm.startswith("Błąd"):
        linie = odpowiedz_llm.strip().split('\n')
        for linia in linie:
            if '|' in linia:
                czesci = linia.split('|', 1)
                if len(czesci) == 2:
                    nazwa = czesci[0].strip()
                    cena_str = czesci[1].strip().replace(',', '.').replace('zł', '').replace('PLN','').strip()
                    try:
                        cena = float(cena_str)
                        if nazwa and len(nazwa) > 1 and cena >= 0:
                            produkty_wyekstrahowane.append({'nazwa': nazwa, 'cena': cena})
                    except ValueError:
                        print(f"⚠️ Pominięto (konwersja ceny): '{linia}'")
    
    return produkty_wyekstrahowane

def sugeruj_kategorie(nazwa_produktu: str, konfiguracja_llm: Dict[str, Any]) -> str:
    """
    Sugeruje kategorię dla produktu na podstawie jego nazwy.
    
    Args:
        nazwa_produktu: Nazwa produktu
        konfiguracja_llm: Konfiguracja LLM
        
    Returns:
        str: Sugerowana kategoria
    """
    system_prompt = """Jesteś ekspertem w kategoryzacji produktów spożywczych i artykułów gospodarstwa domowego. Twoim zadaniem jest przypisanie produktu do jednej z predefiniowanych kategorii."""

    prompt = f"""Przypisz poniższy produkt do jednej z następujących kategorii:
{Nazwa_produktu}

Dostępne kategorie:
{Nazwa_produktu}

Zwróć tylko nazwę kategorii, bez żadnych dodatkowych wyjaśnień."""

    llm = OllamaClient(model=konfiguracja_llm.get('model'),
                      base_url=konfiguracja_llm.get('base_url'))
    
    odpowiedz = llm.zapytaj_llm(prompt, system_prompt,
                               max_tokens=50,
                               temperatura=0.1)
    
    if odpowiedz and not odpowiedz.startswith("Błąd"):
        return odpowiedz.strip()
    return "Inne"

def sugeruj_date_waznosci(nazwa_produktu: str, kategoria: str,
                         konfiguracja_llm: Dict[str, Any]) -> datetime:
    """
    Sugeruje datę ważności dla produktu na podstawie jego nazwy i kategorii.
    
    Args:
        nazwa_produktu: Nazwa produktu
        kategoria: Kategoria produktu
        konfiguracja_llm: Konfiguracja LLM
        
    Returns:
        datetime: Sugerowana data ważności
    """
    system_prompt = """Jesteś ekspertem w zakresie przechowywania żywności i artykułów gospodarstwa domowego. Twoim zadaniem jest oszacowanie typowego okresu przydatności do spożycia dla produktów."""

    prompt = f"""Oszacuj typowy okres przydatności do spożycia dla poniższego produktu:
Nazwa: {nazwa_produktu}
Kategoria: {kategoria}

Zwróć tylko liczbę dni przydatności do spożycia, bez żadnych dodatkowych wyjaśnień."""

    llm = OllamaClient(model=konfiguracja_llm.get('model'),
                      base_url=konfiguracja_llm.get('base_url'))
    
    odpowiedz = llm.zapytaj_llm(prompt, system_prompt,
                               max_tokens=50,
                               temperatura=0.1)
    
    try:
        if odpowiedz and not odpowiedz.startswith("Błąd"):
            dni = int(odpowiedz.strip())
            return datetime.now() + timedelta(days=dni)
    except ValueError:
        pass
    
    # Domyślna data ważności (7 dni) w przypadku błędu
    return datetime.now() + timedelta(days=7) 
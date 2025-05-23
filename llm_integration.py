import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from config import KONFIGURACJA

OLLAMA_URL = KONFIGURACJA["llm"].get("base_url", "http://localhost:11434")
OLLAMA_MODEL = KONFIGURACJA["llm"].get("model", "bielik-1.5b-v3.0-instruct")

class OllamaClient:
    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model or OLLAMA_MODEL
        self.base_url = base_url or OLLAMA_URL

    def zapytaj_llm(self, prompt: str, system_prompt: str = "", max_tokens: int = 1024, temperatura: float = 0.1) -> str:
        # Łączy system prompt i user prompt zgodnie z template Bielika
        full_prompt = f"""<s><|start_header_id|>system<|end_header_id|>\n{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperatura,
                        "num_predict": max_tokens
                    }
                },
                timeout=KONFIGURACJA["llm"].get("timeout_seconds", 60)
            )
            if response.status_code == 200:
                return response.json()["response"].strip()
            else:
                return f"Błąd HTTP {response.status_code}: {response.text}"
        except requests.exceptions.Timeout:
            return "Błąd: Model Ollama nie odpowiedział w wyznaczonym czasie (timeout)."
        except requests.exceptions.RequestException as e:
            return f"Błąd połączenia z LLM Ollama: {e}"


def parsuj_paragon_ai(tekst: str, konfiguracja: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    system_prompt = """Jesteś asystentem do analizy paragonów. Twoim zadaniem jest wyodrębnienie produktów z tekstu paragonu.
    Zwróć TYLKO listę produktów w formacie JSON, bez żadnych dodatkowych wyjaśnień czy komentarzy.
    Format odpowiedzi MUSI być poprawnym JSON array z polskimi znakami:
    [
        {
            "nazwa": "Mleko 3,2%",
            "cena": 4.99,
            "kategoria": "nabiał"
        },
        {
            "nazwa": "Chleb żytni",
            "cena": 6.50,
            "kategoria": "pieczywo"
        }
    ]"""

    prompt = f"""Przeanalizuj poniższy tekst paragonu i wyodrębnij produkty. Zwróć TYLKO listę produktów w formacie JSON.
    Dla każdego produktu podaj:
    - nazwę (zachowaj polskie znaki)
    - cenę (jako float)
    - kategorię (wybierz z: nabiał, mięso, warzywa, owoce, pieczywo, przyprawy, napoje, słodycze, inne)

    Tekst paragonu:
    {tekst}"""

    llm = OllamaClient(model=konfiguracja.get('model'), base_url=konfiguracja.get('base_url'))
    odpowiedz = llm.zapytaj_llm(prompt, system_prompt, max_tokens=konfiguracja.get('max_tokens', 1024), temperatura=konfiguracja.get('temperatura', 0.1))
    
    try:
        # Usuń ewentualne znaki przed i po JSON
        odpowiedz = odpowiedz.strip()
        if odpowiedz.startswith('<tool_call>'):
            odpowiedz = odpowiedz[odpowiedz.find('['):odpowiedz.rfind(']')+1]
        
        # Konwertuj odpowiedź na UTF-8
        odpowiedz = odpowiedz.encode('utf-8').decode('utf-8')
        
        produkty = json.loads(odpowiedz)
        if not isinstance(produkty, list):
            print(f"❌ Nieprawidłowy format odpowiedzi - oczekiwano listy, otrzymano: {type(produkty)}")
            return None
            
        for produkt in produkty:
            if isinstance(produkt.get("cena"), str):
                try:
                    produkt["cena"] = float(produkt["cena"].replace(",", "."))
                except ValueError:
                    produkt["cena"] = 0.0
        return produkty
    except Exception as e:
        print(f"❌ Błąd podczas parsowania paragonu przez AI: {e}")
        print(f"Odpowiedź LLM: {odpowiedz}")
        return None

def sugeruj_kategorie(nazwa_produktu: str, konfiguracja_llm: Dict[str, Any]) -> str:
    system_prompt = "Jesteś ekspertem w kategoryzacji produktów spożywczych i artykułów gospodarstwa domowego. Twoim zadaniem jest przypisanie produktu do jednej z predefiniowanych kategorii."
    prompt = f"""Przypisz poniższy produkt do jednej z następujących kategorii:\n{nazwa_produktu}\n\nDostępne kategorie:\nnabiał, mięso, warzywa, owoce, pieczywo, przyprawy, napoje, słodycze, inne\n\nZwróć tylko nazwę kategorii, bez żadnych dodatkowych wyjaśnień."""
    llm = OllamaClient(model=konfiguracja_llm.get('model'), base_url=konfiguracja_llm.get('base_url'))
    odpowiedz = llm.zapytaj_llm(prompt, system_prompt, max_tokens=50, temperatura=0.1)
    if odpowiedz and not odpowiedz.startswith("Błąd"):
        return odpowiedz.strip().split("\n")[0]
    return "inne"

def sugeruj_date_waznosci(nazwa_produktu: str, kategoria: str, konfiguracja_llm: Dict[str, Any]) -> datetime:
    system_prompt = "Jesteś ekspertem w zakresie przechowywania żywności i artykułów gospodarstwa domowego. Twoim zadaniem jest oszacowanie typowego okresu przydatności do spożycia dla produktów."
    prompt = f"""Oszacuj typowy okres przydatności do spożycia dla poniższego produktu:\nNazwa: {nazwa_produktu}\nKategoria: {kategoria}\n\nZwróć tylko liczbę dni przydatności do spożycia, bez żadnych dodatkowych wyjaśnień."""
    llm = OllamaClient(model=konfiguracja_llm.get('model'), base_url=konfiguracja_llm.get('base_url'))
    odpowiedz = llm.zapytaj_llm(prompt, system_prompt, max_tokens=50, temperatura=0.1)
    try:
        if odpowiedz and not odpowiedz.startswith("Błąd"):
            dni = int([s for s in odpowiedz.split() if s.isdigit()][0])
            return datetime.now() + timedelta(days=dni)
    except Exception:
        pass
    return datetime.now() + timedelta(days=7) 
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import openai
from config import KONFIGURACJA

class LLMIntegrator:
    """
    Klasa do integracji z modelami językowymi (LLM) dla różnych funkcji AI.
    """
    
    def __init__(self):
        """
        Inicjalizuje integrator LLM.
        """
        self.api_key = KONFIGURACJA["llm"]["api_key"]
        openai.api_key = self.api_key
        
        # Ustawienia modelu
        self.model = KONFIGURACJA["llm"]["model"]
        self.temperature = KONFIGURACJA["llm"]["temperature"]
        self.max_tokens = KONFIGURACJA["llm"]["max_tokens"]
    
    def parsuj_paragon_ai(self, tekst: str) -> Optional[List[Dict[str, Any]]]:
        """
        Parsuje tekst paragonu używając AI do wyodrębnienia produktów.
        
        Args:
            tekst: Tekst paragonu z OCR
            
        Returns:
            Optional[List[Dict[str, Any]]]: Lista produktów lub None w przypadku błędu
        """
        try:
            prompt = f"""Przeanalizuj poniższy tekst paragonu i wyodrębnij produkty.
            Dla każdego produktu podaj:
            - nazwę
            - cenę
            - kategorię (wybierz z: nabiał, mięso, warzywa, owoce, pieczywo, przyprawy, napoje, słodycze, inne)
            - sugerowaną datę ważności (w formacie YYYY-MM-DD)
            
            Tekst paragonu:
            {tekst}
            
            Zwróć wynik jako listę obiektów JSON w formacie:
            [
                {{
                    "nazwa": "nazwa produktu",
                    "cena": cena jako float,
                    "kategoria": "kategoria",
                    "data_waznosci": "YYYY-MM-DD"
                }},
                ...
            ]
            
            Jeśli nie możesz rozpoznać jakiegoś pola, użyj null.
            """
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Jesteś asystentem do analizy paragonów. Twoim zadaniem jest wyodrębnienie produktów z tekstu paragonu."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Parsuj odpowiedź
            odpowiedz = response.choices[0].message.content
            produkty = json.loads(odpowiedz)
            
            # Walidacja i czyszczenie danych
            for produkt in produkty:
                # Upewnij się, że cena jest floatem
                if isinstance(produkt.get("cena"), str):
                    try:
                        produkt["cena"] = float(produkt["cena"].replace(",", "."))
                    except ValueError:
                        produkt["cena"] = 0.0
                
                # Upewnij się, że data jest w poprawnym formacie
                if produkt.get("data_waznosci"):
                    try:
                        datetime.strptime(produkt["data_waznosci"], "%Y-%m-%d")
                    except ValueError:
                        produkt["data_waznosci"] = None
            
            return produkty
            
        except Exception as e:
            print(f"❌ Błąd podczas parsowania paragonu przez AI: {e}")
            return None
    
    def sugeruj_kategorie(self, nazwa_produktu: str) -> Optional[List[str]]:
        """
        Sugeruje kategorie dla produktu na podstawie jego nazwy.
        
        Args:
            nazwa_produktu: Nazwa produktu
            
        Returns:
            Optional[List[str]]]: Lista sugerowanych kategorii lub None w przypadku błędu
        """
        try:
            prompt = f"""Sugeruj kategorie dla produktu: {nazwa_produktu}
            
            Dostępne kategorie:
            - nabiał
            - mięso
            - warzywa
            - owoce
            - pieczywo
            - przyprawy
            - napoje
            - słodycze
            - inne
            
            Zwróć maksymalnie 3 najbardziej prawdopodobne kategorie jako listę JSON.
            """
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Jesteś asystentem do kategoryzacji produktów spożywczych."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            kategorie = json.loads(response.choices[0].message.content)
            return kategorie[:3]  # Zwróć max 3 kategorie
            
        except Exception as e:
            print(f"❌ Błąd podczas sugerowania kategorii: {e}")
            return None
    
    def sugeruj_date_waznosci(self, nazwa_produktu: str, kategoria: str) -> Optional[str]:
        """
        Sugeruje datę ważności dla produktu.
        
        Args:
            nazwa_produktu: Nazwa produktu
            kategoria: Kategoria produktu
            
        Returns:
            Optional[str]: Sugerowana data ważności w formacie YYYY-MM-DD lub None w przypadku błędu
        """
        try:
            prompt = f"""Sugeruj datę ważności dla produktu:
            Nazwa: {nazwa_produktu}
            Kategoria: {kategoria}
            
            Zwróć datę w formacie YYYY-MM-DD.
            Data powinna być realistyczna, biorąc pod uwagę typ produktu.
            """
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Jesteś asystentem do określania dat ważności produktów spożywczych."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            data = response.choices[0].message.content.strip()
            
            # Walidacja formatu daty
            try:
                datetime.strptime(data, "%Y-%m-%d")
                return data
            except ValueError:
                print(f"⚠️ Nieprawidłowy format daty: {data}")
                return None
            
        except Exception as e:
            print(f"❌ Błąd podczas sugerowania daty ważności: {e}")
            return None
    
    def sugeruj_przepisy(self, produkty: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        """
        Sugeruje przepisy na podstawie dostępnych produktów.
        
        Args:
            produkty: Lista dostępnych produktów
            
        Returns:
            Optional[List[Dict[str, Any]]]: Lista sugerowanych przepisów lub None w przypadku błędu
        """
        try:
            # Przygotuj listę produktów do promptu
            produkty_text = "\n".join([
                f"- {p['nazwa']} ({p['kategoria']})"
                for p in produkty
            ])
            
            prompt = f"""Sugeruj przepisy na podstawie dostępnych produktów:
            
            Dostępne produkty:
            {produkty_text}
            
            Dla każdego przepisu podaj:
            - nazwę
            - listę potrzebnych produktów
            - krótki opis przygotowania
            - szacowany czas przygotowania w minutach
            
            Zwróć listę przepisów jako JSON w formacie:
            [
                {{
                    "nazwa": "nazwa przepisu",
                    "produkty": ["produkt1", "produkt2", ...],
                    "przygotowanie": "krótki opis",
                    "czas": czas w minutach
                }},
                ...
            ]
            """
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Jesteś asystentem kulinarnym. Twoim zadaniem jest sugerowanie przepisów na podstawie dostępnych produktów."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            przepisy = json.loads(response.choices[0].message.content)
            return przepisy
            
        except Exception as e:
            print(f"❌ Błąd podczas sugerowania przepisów: {e}")
            return None

def parsuj_paragon_ai(tekst: str, konfiguracja: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """
    Funkcja pomocnicza do parsowania paragonu przez AI.
    
    Args:
        tekst: Tekst paragonu
        konfiguracja: Konfiguracja LLM
        
    Returns:
        Optional[List[Dict[str, Any]]]: Lista produktów lub None w przypadku błędu
    """
    integrator = LLMIntegrator()
    return integrator.parsuj_paragon_ai(tekst)

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
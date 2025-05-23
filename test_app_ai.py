#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test AI w aplikacji spiżarni po zmianie modelu
"""

from llm_integration import sugeruj_kategorie, sugeruj_date_waznosci
from config import KONFIGURACJA
from datetime import datetime

def test_ai_funkcje():
    """Test funkcji AI używanych w aplikacji"""
    print("=== TEST FUNKCJI AI W APLIKACJI ===\n")
    
    llm_config = KONFIGURACJA["llm"]
    
    # Test 1: Kategoryzacja różnych produktów
    print("--- Test kategoryzacji produktów ---")
    produkty_test = [
        "mleko 3.2%",
        "chleb żytni", 
        "kurczak filet",
        "pomidory",
        "coca cola",
        "masło"
    ]
    
    for produkt in produkty_test:
        try:
            kategoria = sugeruj_kategorie(produkt, llm_config)
            print(f"'{produkt}' → {kategoria}")
        except Exception as e:
            print(f"❌ Błąd dla '{produkt}': {e}")
    
    # Test 2: Sugestie dat ważności
    print("\n--- Test sugestii dat ważności ---")
    produkty_z_kategoriami = [
        ("mleko", "nabiał"),
        ("chleb", "pieczywo"), 
        ("kurczak", "mięso"),
        ("pomidory", "warzywa"),
        ("ryż", "produkty suche")
    ]
    
    for produkt, kategoria in produkty_z_kategoriami:
        try:
            data_waznosci = sugeruj_date_waznosci(produkt, kategoria, llm_config)
            dni_od_dzis = (data_waznosci - datetime.now()).days
            print(f"'{produkt}' ({kategoria}) → {data_waznosci.strftime('%Y-%m-%d')} ({dni_od_dzis} dni)")
        except Exception as e:
            print(f"❌ Błąd dla '{produkt}': {e}")
    
    print("\n=== PODSUMOWANIE ===")
    print("Jeśli powyższe testy działają - aplikacja będzie działać z AI!")
    print("Uruchom: python3 main.py i wybierz opcję 1 (Dodaj produkt)")

if __name__ == "__main__":
    test_ai_funkcje()
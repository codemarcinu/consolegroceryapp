#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Szybki test konfiguracji Bielik dla aplikacji spiżarni
"""

import requests
import json

def test_ollama_connection():
    """Test połączenia z Ollama"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print("✅ Ollama działa")
            print("Dostępne modele:")
            for model in models:
                print(f"  - {model.get('name', 'Unknown')}")
            return True
        else:
            print(f"❌ Ollama odpowiedział z kodem: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Błąd połączenia z Ollama: {e}")
        return False

def test_bielik_model(model_name="bielik"):
    """Test konkretnego modelu Bielik"""
    print(f"\n=== TEST MODELU: {model_name} ===")
    
    tests = [
        {
            "name": "Test podstawowy",
            "prompt": "Napisz krótko: ile mamy pór roku w Polsce?",
            "expected_keywords": ["cztery", "4", "wiosna", "lato", "jesień", "zima"]
        },
        {
            "name": "Test kategoryzacji",
            "prompt": "Przypisz produkt 'mleko 3.2%' do jednej kategorii: nabiał, mięso, warzywa, owoce, inne. Odpowiedz tylko nazwą kategorii.",
            "expected_keywords": ["nabiał"]
        },
        {
            "name": "Test daty ważności", 
            "prompt": "Ile dni przydatności ma świeże mleko w lodówce? Odpowiedz tylko liczbą.",
            "expected_keywords": ["5", "6", "7", "8", "9", "10"]
        }
    ]
    
    for test in tests:
        print(f"\n--- {test['name']} ---")
        print(f"Prompt: {test['prompt']}")
        
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model_name,
                    "prompt": test['prompt'],
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 50
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "").strip()
                print(f"Odpowiedź: '{answer}'")
                
                # Sprawdź czy odpowiedź zawiera oczekiwane słowa kluczowe
                answer_lower = answer.lower()
                found_keywords = [kw for kw in test['expected_keywords'] if kw in answer_lower]
                
                if found_keywords:
                    print(f"✅ Test zaliczony (znalezione: {found_keywords})")
                else:
                    print(f"⚠️ Test niepewny (brak słów kluczowych: {test['expected_keywords']})")
            else:
                print(f"❌ Błąd HTTP: {response.status_code}")
                print(f"Odpowiedź: {response.text}")
                
        except Exception as e:
            print(f"❌ Błąd testu: {e}")

def test_template_format(model_name="bielik"):
    """Sprawdza jaki template używa model"""
    try:
        # Próba sprawdzenia template (może nie działać ze wszystkimi wersjami Ollama)
        response = requests.post(
            "http://localhost:11434/api/show",
            json={"name": model_name},
            timeout=10
        )
        
        if response.status_code == 200:
            model_info = response.json()
            template = model_info.get("template", "")
            
            print(f"\n=== TEMPLATE MODELU: {model_name} ===")
            if template:
                print("Template:")
                print(template)
                
                # Sprawdź typ template
                if "<|im_start|>" in template and "<|im_end|>" in template:
                    print("✅ Używa ChatML template (prawidłowy dla Bielik)")
                elif "<|start_header_id|>" in template and "<|eot_id|>" in template:
                    print("⚠️ Używa Llama3 template (może być nieprawidłowy dla Bielik)")
                else:
                    print("❓ Nieznany format template")
            else:
                print("❓ Nie można odczytać template")
        else:
            print(f"❌ Nie można sprawdzić template: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Błąd sprawdzania template: {e}")

if __name__ == "__main__":
    print("=== DIAGNOSTYKA BIELIK DLA APLIKACJI SPIŻARNI ===\n")
    
    # Test 1: Połączenie z Ollama
    if not test_ollama_connection():
        print("\n❌ Nie można kontynuować - Ollama nie działa")
        exit(1)
    
    # Test 2: Template
    test_template_format("bielik")
    
    # Test 3: Funkcjonalność modelu
    test_bielik_model("bielik")
    
    # Test 4: Drugi model jeśli istnieje
    print("\n" + "="*60)
    test_bielik_model("bielik-local-q8")
    
    print("\n=== PODSUMOWANIE ===")
    print("1. Jeśli testy przechodzą ✅ - aplikacja powinna działać")
    print("2. Jeśli są ⚠️ lub ❌ - sprawdź Modfile i template")
    print("3. Uruchom aplikację i sprawdź opcję kategoryzacji")
    print("\nAby naprawić template, użyj poprawionego Modfile z sugestii!")
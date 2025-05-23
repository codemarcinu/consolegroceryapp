#!/bin/bash

# Kolory dla lepszej czytelności
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Asystent Zakupów i Spiżarni v2 - Skrypt instalacyjny ===${NC}\n"

# Sprawdź czy Python 3.8+ jest zainstalowany
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 nie jest zainstalowany!${NC}"
    echo "Zainstaluj Python 3.8 lub nowszy i spróbuj ponownie."
    exit 1
fi

# Sprawdź czy pip jest zainstalowany
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 nie jest zainstalowany!${NC}"
    echo "Zainstaluj pip3 i spróbuj ponownie."
    exit 1
fi

# Sprawdź czy venv jest zainstalowany
if ! python3 -c "import venv" &> /dev/null; then
    echo -e "${RED}❌ Moduł venv nie jest zainstalowany!${NC}"
    echo "Zainstaluj python3-venv i spróbuj ponownie."
    exit 1
fi

# Utwórz wirtualne środowisko
echo -e "${YELLOW}Tworzenie wirtualnego środowiska...${NC}"
python3 -m venv venv

# Aktywuj wirtualne środowisko
echo -e "${YELLOW}Aktywowanie wirtualnego środowiska...${NC}"
source venv/bin/activate

# Uaktualnij pip
echo -e "${YELLOW}Uaktualnianie pip...${NC}"
pip install --upgrade pip

# Zainstaluj wymagane pakiety
echo -e "${YELLOW}Instalowanie wymaganych pakietów...${NC}"
pip install -r requirements.txt

# Sprawdź czy Ollama jest zainstalowane
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}⚠️ Ollama nie jest zainstalowane.${NC}"
    echo "Czy chcesz zainstalować Ollama? (t/n)"
    read -r odpowiedz
    if [[ $odpowiedz =~ ^[Tt]$ ]]; then
        echo -e "${YELLOW}Instalowanie Ollama...${NC}"
        curl https://ollama.ai/install.sh | sh
        
        echo -e "${YELLOW}Uruchamianie serwera Ollama...${NC}"
        ollama serve &
        OLLAMA_PID=$!
        
        # Poczekaj na uruchomienie serwera
        echo -e "${YELLOW}Czekanie na uruchomienie serwera Ollama...${NC}"
        sleep 5
    else
        echo -e "${YELLOW}⚠️ Uwaga: Aplikacja może nie działać poprawnie bez Ollama!${NC}"
    fi
else
    # Sprawdź czy serwer Ollama jest uruchomiony
    if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo -e "${YELLOW}Uruchamianie serwera Ollama...${NC}"
        ollama serve &
        OLLAMA_PID=$!
        
        # Poczekaj na uruchomienie serwera
        echo -e "${YELLOW}Czekanie na uruchomienie serwera Ollama...${NC}"
        sleep 5
    fi
fi

# Utwórz wymagane katalogi
echo -e "${YELLOW}Tworzenie wymaganych katalogów...${NC}"
mkdir -p data/archive
mkdir -p paragony/nowe
mkdir -p paragony/przetworzone
mkdir -p paragony/bledy

# Uruchom aplikację
echo -e "${GREEN}=== Uruchamianie aplikacji ===${NC}"
python main.py

# Zatrzymaj serwer Ollama jeśli został uruchomiony przez skrypt
if [ -n "$OLLAMA_PID" ]; then
    echo -e "${YELLOW}Zatrzymywanie serwera Ollama...${NC}"
    kill $OLLAMA_PID
fi

# Deaktywuj wirtualne środowisko
deactivate 
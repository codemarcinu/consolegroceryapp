from datetime import datetime
from typing import Optional

class Produkt:
    """
    Klasa reprezentująca produkt w spiżarni.
    
    Atrybuty:
        nazwa (str): Nazwa produktu
        kategoria (str): Kategoria produktu (np. Nabiał, Mięso/Wędliny)
        data_waznosci (datetime): Data ważności produktu
        cena (float, opcjonalnie): Cena zakupu produktu
        data_dodania (datetime): Data dodania produktu do spiżarni
        zuzyty (bool): Status wskazujący, czy produkt został zużyty
        id_paragonu (str, opcjonalnie): Identyfikator paragonu, z którego pochodzi produkt
    """
    
    def __init__(self, 
                 nazwa: str,
                 kategoria: str,
                 data_waznosci: datetime,
                 cena: Optional[float] = None,
                 data_dodania: Optional[datetime] = None,
                 zuzyty: bool = False,
                 id_paragonu: Optional[str] = None):
        """
        Inicjalizuje nowy obiekt Produkt.
        
        Args:
            nazwa: Nazwa produktu
            kategoria: Kategoria produktu
            data_waznosci: Data ważności produktu
            cena: Cena zakupu produktu (opcjonalnie)
            data_dodania: Data dodania produktu do spiżarni (opcjonalnie, domyślnie teraz)
            zuzyty: Status zużycia produktu (domyślnie False)
            id_paragonu: Identyfikator paragonu (opcjonalnie)
        """
        self.nazwa = nazwa
        self.kategoria = kategoria
        self.data_waznosci = data_waznosci
        self.cena = cena
        self.data_dodania = data_dodania or datetime.now()
        self.zuzyty = zuzyty
        self.id_paragonu = id_paragonu
    
    def to_dict(self) -> dict:
        """
        Konwertuje obiekt Produkt do słownika.
        
        Returns:
            dict: Słownik reprezentujący produkt
        """
        return {
            'nazwa': self.nazwa,
            'kategoria': self.kategoria,
            'data_waznosci': self.data_waznosci.isoformat(),
            'cena': self.cena,
            'data_dodania': self.data_dodania.isoformat(),
            'zuzyty': self.zuzyty,
            'id_paragonu': self.id_paragonu
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Produkt':
        """
        Tworzy obiekt Produkt ze słownika.
        
        Args:
            data: Słownik zawierający dane produktu
            
        Returns:
            Produkt: Nowy obiekt Produkt
        """
        return cls(
            nazwa=data['nazwa'],
            kategoria=data['kategoria'],
            data_waznosci=datetime.fromisoformat(data['data_waznosci']),
            cena=data.get('cena'),
            data_dodania=datetime.fromisoformat(data['data_dodania']),
            zuzyty=data.get('zuzyty', False),
            id_paragonu=data.get('id_paragonu')
        )
    
    def __str__(self) -> str:
        """
        Zwraca czytelną reprezentację produktu.
        
        Returns:
            str: Sformatowany string z informacjami o produkcie
        """
        return (f"{self.nazwa} ({self.kategoria}) - "
                f"Wazność do: {self.data_waznosci.strftime('%Y-%m-%d')}"
                f"{f' - Cena: {self.cena:.2f} zł' if self.cena else ''}") 
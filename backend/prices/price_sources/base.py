from abc import ABC, abstractmethod
from typing import List, Dict


class BasePriceSource(ABC):
    name: str

    @abstractmethod
    def search(self, query: str) -> List[Dict]:
        raise NotImplementedError


def parse_brl_price(raw: str) -> float:
    if raw is None:
        raise ValueError("Preço vazio")

    cleaned = raw.replace("R$", "")
    cleaned = cleaned.replace("\xa0", "")  # NBSP
    cleaned = cleaned.replace(" ", "")
    cleaned = cleaned.replace(".", "")
    cleaned = cleaned.strip()
    cleaned = cleaned.replace(",", ".")
    return float(cleaned)

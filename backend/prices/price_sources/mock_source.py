from typing import List, Dict, Any
from prices.price_sources.base import BasePriceSource


class MockPriceSource(BasePriceSource):
    name = "Loja Mock"

    def search(self, query: str) -> List[Dict[str, Any]]:
        # Em um cenário real, você faria requests aqui.
        # No MVP v1, devolve algo "coerente"
        return [
            {
                "store": self.name,
                "source": "mock",
                "id": "MOCK-1",
                "title": f"{query} - Versão Básica",
                "price": 3999.90,
                "currency": "BRL",
                "url": "https://loja-mock.com/produto/1",
                "thumbnail": None,
            },
            {
                "store": self.name,
                "source": "mock",
                "id": "MOCK-2",
                "title": f"{query} - Versão Premium",
                "price": 4599.90,
                "currency": "BRL",
                "url": "https://loja-mock.com/produto/2",
                "thumbnail": None,
            },
        ]

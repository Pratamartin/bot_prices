# prices/price_sources/mock_source_b.py
from typing import List, Dict, Any
from prices.price_sources.base import BasePriceSource


class MockPriceSourceB(BasePriceSource):
    name = "Loja Mock B"

    def search(self, query: str) -> List[Dict[str, Any]]:
        return [
            {
                "store": self.name,
                "source": "mock_b",
                "id": "MOCKB-1",
                "title": f"{query} - Edição Especial",
                "price": 3899.90,
                "currency": "BRL",
                "url": "https://loja-mock-b.com/produto/1",
                "thumbnail": None,
            },
        ]

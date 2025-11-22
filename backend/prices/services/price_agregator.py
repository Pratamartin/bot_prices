# prices/services/price_aggregator.py
from typing import List, Dict, Any
from prices.price_sources.mock_source import MockPriceSource
from prices.price_sources.mock_source_b import MockPriceSourceB
from prices.price_sources.http_store_source import HttpStoreSource
# depois você adiciona MercadoLivreAPISource, AmazonSource etc.


class PriceAggregator:
    def __init__(self) -> None:
        self.sources = [
            MockPriceSource(),
            MockPriceSourceB(),
            HttpStoreSource(),
        ]

    def search_all(self, query: str) -> Dict[str, Any]:
        all_results: List[Dict[str, Any]] = []

        for source in self.sources:
            results = source.search(query)
            all_results.extend(results)

        if not all_results:
            return {
                "query": query,
                "results": [],
                "best": None,
            }

        best = min(all_results, key=lambda x: x["price"])

        return {
            "query": query,
            "results": all_results,
            "best": best,
        }

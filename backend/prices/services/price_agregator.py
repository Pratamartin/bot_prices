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

    def _tokenize(self, text: str) -> List[str]:
        text = (text or "").lower()
        # split simples por espaço; dá pra melhorar depois
        return [t for t in text.split() if t]

    def _is_relevant(self, query_tokens: List[str], title: str) -> bool:
        """
        Estratégia simples:
        - título vira lower
        - consideramos relevante se pelo menos X% dos tokens da query estiverem no título
        """
        if not title:
            return False

        title_l = title.lower()
        if not query_tokens:
            return True

        hits = 0
        for token in query_tokens:
            if token in title_l:
                hits += 1

        # por enquanto: pelo menos metade dos tokens devem aparecer no título
        return hits >= max(1, len(query_tokens) // 2)

    def search_all(self, query: str) -> Dict[str, Any]:
        all_results: List[Dict[str, Any]] = []

        for source in self.sources:
            results = source.search(query)
            all_results.extend(results)

        query_tokens = self._tokenize(query)

        # marca relevância
        for item in all_results:
            title = item.get("title", "")
            item["relevant"] = self._is_relevant(query_tokens, title)

        relevant_results = [r for r in all_results if r.get("relevant")]

        if not all_results:
            return {
                "query": query,
                "results": [],
                "best": None,
            }

        if not relevant_results:
            # se nada for considerado relevante, a gente volta a usar tudo
            relevant_results = all_results

        best = min(relevant_results, key=lambda x: x["price"])

        return {
            "query": query,
            "results": all_results,      # com campo "relevant" em cada item
            "best": best,
        }

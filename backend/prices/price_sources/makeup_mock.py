# prices/price_sources/makeup_mock.py
import re
from typing import List, Dict, Any

from prices.price_sources.base import BasePriceSource
from prices.mock_data.makeup_products import MOCK_MAKEUP_PRODUCTS


class MakeupMockSource(BasePriceSource):
    name = "Makeup Mock Store"

    def _normalize(self, s: str) -> str:
        return re.sub(r"\s+", " ", s or "").strip().lower()

    def search(self, query: str) -> List[Dict[str, Any]]:
        q_norm = self._normalize(query)
        if not q_norm:
            return []

        tokens = q_norm.split()
        results: List[Dict[str, Any]] = []

        for p in MOCK_MAKEUP_PRODUCTS:
            title_norm = self._normalize(p["title"])

            # contagem de tokens que aparecem no título
            hits = sum(1 for t in tokens if t in title_norm)
            if hits == 0:
                continue

            score = hits / len(tokens)

            item = {
                "store": p["store"],
                "source": p["source"],
                "id": p["id"],
                "title": p["title"],
                "price": float(p["price"]),
                "currency": p.get("currency", "BRL"),
                "url": p.get("url"),
                "thumbnail": p.get("thumbnail"),
                "relevance_score": score,
                "relevant": True,  # tudo que passou no filtro é relevante, por enquanto
            }
            results.append(item)

        # ordena do mais relevante pro menos
        results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return results

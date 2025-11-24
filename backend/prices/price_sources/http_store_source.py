# prices/price_sources/http_store_source.py
from typing import List, Dict, Any
import logging
import urllib.parse
import requests

from prices.price_sources.base import BasePriceSource

logger = logging.getLogger(__name__)


class HttpStoreSource(BasePriceSource):
    """
    Exemplo de fonte real chamando uma API HTTP externa.
    Aqui uso uma API pública genérica como "loja de teste".
    """

    name = "Loja HTTP Exemplo"
    SEARCH_URL = "https://dummyjson.com/products/search"

    def search(self, query: str) -> List[Dict[str, Any]]:
        q_clean = urllib.parse.unquote_plus(query)

        params = {
            "q": q_clean,
            "limit": 10,
        }

        try:
            resp = requests.get(self.SEARCH_URL, params=params, timeout=10)
        except requests.RequestException as e:
            logger.exception("[%s] erro de rede: %s", self.name, e)
            return []

        if resp.status_code != 200:
            logger.error(
                "[%s] erro HTTP %s: %s",
                self.name,
                resp.status_code,
                resp.text,
            )
            return []

        data = resp.json()

        results: List[Dict[str, Any]] = []
        for product in data.get("products", []):  
            results.append(
                {
                    "store": self.name,
                    "source": "http_store_example",
                    "id": str(product.get("id")),
                    "title": product.get("title") or q_clean,
                    "price": float(product.get("price", 0)),
                    "currency": "BRL",
                    "url": product.get("url") or "",
                    "thumbnail": product.get("thumbnail"),
                }
            )

        return results

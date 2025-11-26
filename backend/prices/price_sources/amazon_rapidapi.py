# prices/price_sources/amazon_rapidapi.py
from typing import List, Dict, Any
import logging
import os
import urllib.parse

import requests

from prices.price_sources.base import BasePriceSource

logger = logging.getLogger(__name__)


class AmazonRapidAPISource(BasePriceSource):
    name = "Amazon (via RapidAPI)"
    BASE_URL = "https://real-time-amazon-data.p.rapidapi.com/search"

    def __init__(self) -> None:
        super().__init__()
        self.rapidapi_key = os.environ.get("RAPIDAPI_KEY")
        self.rapidapi_host = os.environ.get(
            "RAPIDAPI_HOST", "real-time-amazon-data.p.rapidapi.com"
        )

        if not self.rapidapi_key:
            logger.warning(
                "[AmazonRapidAPISource] RAPIDAPI_KEY não configurado; "
                "essa fonte não irá retornar resultados."
            )

    def search(self, query: str) -> List[Dict[str, Any]]:
        if not self.rapidapi_key:
            return []

        q_clean = urllib.parse.unquote_plus(query)

        params = {
            "query": q_clean,
            "page": "1",
            "country": "BR",
            "sort_by": "RELEVANCE",
            "product_condition": "ALL",
            "is_prime": "false",
            "deals_and_discounts": "NONE",
            "language": "pt_BR",
        }

        headers = {
            "x-rapidapi-key": self.rapidapi_key,
            "x-rapidapi-host": self.rapidapi_host,
        }

        try:
            resp = requests.get(
                self.BASE_URL,
                params=params,
                headers=headers,
                timeout=15,
            )
        except requests.RequestException as e:
            logger.exception("[AmazonRapidAPISource] Erro de rede: %s", e)
            return []

        logger.info(
            "[AmazonRapidAPISource] HTTP %s - URL final: %s",
            resp.status_code,
            resp.url,
        )

        if resp.status_code != 200:
            logger.error(
                "[AmazonRapidAPISource] Erro HTTP %s: %s",
                resp.status_code,
                resp.text,
            )
            return []

        data = resp.json()

        products = data.get("data", {}).get("products") or []

        logger.info(
            "[AmazonRapidAPISource] Produtos retornados: %s",
            len(products),
        )

        results: List[Dict[str, Any]] = []

        for p in products:
            title = p.get("product_title") or q_clean
            url = p.get("product_url") or ""
            thumb = p.get("product_photo") or (p.get("product_photos") or [None])[0]
            price_str = p.get("product_price")
            currency = p.get("currency") or "BRL"

            price_value = _parse_price(price_str)
            if price_value is None:
                continue

            results.append(
                {
                    "store": self.name,
                    "source": "amazon_rapidapi",
                    "id": p.get("asin") or p.get("product_id"),
                    "title": title,
                    "price": price_value,
                    "currency": currency,
                    "url": url,
                    "thumbnail": thumb,
                }
            )

        return results
    



def _parse_price(price_str: Any) -> float | None:
    if not price_str:
        return None

    s = str(price_str)

    # remove NBSP e outros espaços "estranhos"
    s = s.replace("\u00a0", " ")

    s = s.strip()

    # remove símbolos de moeda
    for ch in ["R$", "US$", "$", "€"]:
        s = s.replace(ch, "")
    s = s.strip()

    s = s.replace(" ", "")

    try:
        # casos BR: 1.234,56  -> 1234.56
        if "," in s and "." in s:
            s_norm = s.replace(".", "").replace(",", ".")
            return float(s_norm)
        # casos tipo 1234,56
        if "," in s and "." not in s:
            s_norm = s.replace(",", ".")
            return float(s_norm)
        # casos tipo 1234.56
        return float(s)
    except ValueError:
        logger.warning("[AmazonRapidAPISource] Falha ao parsear preço: %r", price_str)

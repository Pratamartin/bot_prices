# prices/price_sources/mercado_livre_rapidapi.py
import os
from typing import List, Dict, Any

import requests

from prices.price_sources.base import BasePriceSource


class MercadoLivreRapidAPISource(BasePriceSource):
    name = "Mercado Livre (via RapidAPI)"
    SEARCH_URL = "https://mercado-libre7.p.rapidapi.com/listings_for_search"

    def _parse_price(self, raw) -> float | None:
        """
        Converte preço que pode vir como string 'R$ 2.699,10' ou número.
        """
        if raw is None:
            return None

        if isinstance(raw, (int, float)):
            try:
                return float(raw)
            except (TypeError, ValueError):
                return None

        if isinstance(raw, str):
            s = raw.strip()
            # remove símbolo de moeda e espaço
            s = s.replace("R$", "").replace("US$", "").strip()
            # remove separador de milhar e troca vírgula por ponto
            s = s.replace(".", "").replace(",", ".")
            try:
                return float(s)
            except ValueError:
                return None

        return None

    def search(self, query: str) -> List[Dict[str, Any]]:
        api_key = os.environ.get("RAPIDAPI_KEY")
        if not api_key:
            # sem key, sem resultado
            return []

        params = {
            "search_str": query,
            "country": "br",
            "sort_by": "price_asc",  # mais barato primeiro
            "page_num": 1,
        }
        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "mercado-libre7.p.rapidapi.com",
        }

        try:
            resp = requests.get(self.SEARCH_URL, headers=headers, params=params, timeout=15)
            print(resp)  # para debug, pode remover depois
        except requests.RequestException:
            return []

        if resp.status_code != 200:
            # você pode logar se quiser
            return []

        data = resp.json()

        products = data.get("data") or []

        print(products)  

        results: List[Dict[str, Any]] = []

        for p in products:
            title = p.get("title") or ""
            raw_price = p.get("price")
            price = self._parse_price(raw_price)
            if price is None:
                continue

            currency_raw = p.get("currency") or "R$"
            currency = "BRL" if "R" in currency_raw else currency_raw

            url = p.get("url")  
            thumbnail = None  

            item_id = p.get("id")

            results.append(
                {
                    "store": self.name,
                    "source": "mercado_livre_rapidapi",
                    "id": item_id,
                    "title": title,
                    "price": price,
                    "currency": currency,
                    "url": url,
                    "thumbnail": thumbnail,
                }
            )

        return results

import logging
import os
import re
from typing import Any, Dict, List, Optional

import requests

from prices.price_sources.base import BasePriceSource

logger = logging.getLogger(__name__)


def _normalize_text(s: str) -> str:
    s = s or ""
    s = s.lower()
    s = re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _parse_price(price_str: Optional[str]) -> Optional[float]:
    if not price_str:
        return None

    s = price_str.strip()
    # remove “agora” e outros textos
    s = re.sub(r"\bagora\b", "", s, flags=re.IGNORECASE).strip()
    # remove tudo que não é dígito, vírgula ou ponto
    s = re.sub(r"[^\d,\.]", "", s)

    if "," in s and "." in s:
        # provavelmente 1.234,56
        s = s.replace(".", "").replace(",", ".")
    elif "," in s and "." not in s:
        # 59,90
        s = s.replace(",", ".")

    try:
        return float(s)
    except ValueError:
        logger.warning("Não consegui converter preço: %r", price_str)
        return None


class SerperShoppingSource(BasePriceSource):
    name = "Google Shopping (Serper)"
    URL = "https://google.serper.dev/shopping"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("SERPER_API_KEY") or ""

    def _relevance_score(self, query: str, title: str) -> float:
        q_norm = _normalize_text(query)
        t_norm = _normalize_text(title)

        if not q_norm or not t_norm:
            return 0.0

        q_tokens = q_norm.split()
        hits = sum(1 for tok in q_tokens if tok in t_norm)
        base = hits / len(q_tokens)

        first = q_tokens[0]
        if t_norm.startswith(first):
            base += 0.1

        return base

    def search(self, query: str) -> List[Dict[str, Any]]:
        if not self.api_key:
            logger.warning("SERPER_API_KEY não configurada; Serper desativado.")
            return []

        q = (query or "").strip()
        if not q:
            return []

        payload = {
            "q": q,
            "gl": "br",
            "hl": "pt-br",
            "num": 20,   # você pode reduzir para economizar créditos
        }
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(self.URL, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.exception("[Serper] erro HTTP na busca: %s", e)
            return []

        try:
            data = resp.json()
        except ValueError:
            logger.exception("[Serper] resposta não é JSON válido")
            return []

        items = data.get("shopping") or []
        results: List[Dict[str, Any]] = []

        for item in items:
            title = item.get("title") or ""
            source = item.get("source") or "Loja"
            link = item.get("link")
            thumb = item.get("imageUrl")
            raw_price = item.get("price")

            price = _parse_price(raw_price)
            if price is None:
                continue

            score = self._relevance_score(q, title)

            results.append(
                {
                    "store": source,
                    "source": "serper_shopping",
                    "id": item.get("productId") or item.get("position") or link or title,
                    "title": title,
                    "price": price,
                    "currency": "BRL",
                    "url": link,
                    "thumbnail": thumb,
                    "relevance_score": score,
                    "relevant": True,
                }
            )

        # ordenar do mais relevante pro menos relevante
        results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return results

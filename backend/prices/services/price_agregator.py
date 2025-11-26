from typing import List, Dict, Any
import logging

from prices.price_sources.amazon_rapidapi import AmazonRapidAPISource

from prices.domain.relevance_terms import (
    ACCESSORY_BAD_WORDS,
    PS5_ACCESSORY_PHRASES,
    PS5_CONSOLE_HINTS,
)

logger = logging.getLogger(__name__)



class PriceAggregator:
    def __init__(self) -> None:
        self.sources = [
            AmazonRapidAPISource(),
        ]

    def _tokenize(self, text: str) -> List[str]:
        text = (text or "").lower()
        return [t for t in text.split() if t]
    
    def _looks_like_accessory(self, title: str) -> bool:
        t = (title or "").lower()
        return any(bad in t for bad in ACCESSORY_BAD_WORDS)
    
    def _get_query_profile(self, tokens: List[str]) -> str | None:
        t = [x.lower() for x in tokens]

        if "iphone" in t:
            return "phone"

        if "ps5" in t or ("playstation" in t and "5" in t):
            return "ps5_console"

        return None
    
    def _looks_like_ps5_game(self, title_l: str) -> bool:
        if " - playstation 5" in title_l and "console" not in title_l:
            return True

        if "ps5" in title_l:
            if not any(hint in title_l for hint in PS5_CONSOLE_HINTS):
                return True

        return False

    
    def _looks_like_ps5_accessory(self, title_l: str) -> bool:
        for phrase in PS5_ACCESSORY_PHRASES:
            if phrase in title_l:
                return True
        return False
    
    def _is_ps5_console(self, item: dict) -> bool:
        """
        Decide se esse produto é de fato um CONSOLE PS5.
        Usa título + preço.
        """
        title = item.get("title") or ""
        title_l = title.lower()
        price = float(item.get("price") or 0)

        if price < 1000:
            return False

        if "ps5" not in title_l and "playstation 5" not in title_l and "playstation®5" not in title_l:
            return False

        if "console" in title_l:
            return True

        if any(hint in title_l for hint in PS5_CONSOLE_HINTS):
            return True

        return False
    
    def _normalize_title(self, title: str) -> str:
        t = (title or "").lower()

        replacements = [
            ("playstation®5", "ps5"),
            ("playstation 5", "ps5"),
            ("ps 5", "ps5"),
        ]
        for old, new in replacements:
            t = t.replace(old, new)

        return t

    
    def _relevance_score(self, query_tokens: list[str], title: str) -> float:
        if not title:
            return 0.0

        title_l = self._normalize_title(title)
        profile = self._get_query_profile(query_tokens)

        if not query_tokens:
            base = 1.0
        else:
            hits = sum(1 for token in query_tokens if token in title_l)
            base = hits / len(query_tokens)

        if any(bad in title_l for bad in ACCESSORY_BAD_WORDS):
            base *= 0.2

        if profile == "ps5_console":

            if self._looks_like_ps5_game(title_l):
                base *= 0.05

            if self._looks_like_ps5_accessory(title_l):
                base *= 0.01

            if any(hint in title_l for hint in PS5_CONSOLE_HINTS):
                base += 0.2

        first_token = query_tokens[0] if query_tokens else ""
        if first_token and title_l.startswith(first_token):
            base += 0.1

        return base


    def search_all(self, query: str) -> Dict[str, Any]:
        all_results: List[Dict[str, Any]] = []

        for source in self.sources:
            results = source.search(query)
            logger.info("[%s] retornou %d resultados", source.name, len(results))
            all_results.extend(results)

        query_tokens = self._tokenize(query)
        profile = self._get_query_profile(query_tokens)

        for item in all_results:
            title = item.get("title", "")
            score = self._relevance_score(query_tokens, title)
            item["relevance_score"] = score

        relevant_results = [r for r in all_results if r.get("relevance_score", 0) >= 0.4]

        if not all_results:
            return {
                "query": query,
                "results": [],
                "best": None,
            }

        if not relevant_results:
            relevant_results = sorted(all_results, key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        if profile == "ps5_console":
            console_candidates = [r for r in relevant_results if self._is_ps5_console(r)]
            if console_candidates:
                relevant_results = console_candidates

        best = min(relevant_results, key=lambda x: x["price"])

        all_results_sorted = sorted(all_results, key=lambda x: x.get("relevance_score", 0), reverse=True)

        return {
            "query": query,
            "results": all_results_sorted,
            "best": best,
        }
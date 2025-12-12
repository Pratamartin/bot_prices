from typing import List, Dict, Any
import logging
from statistics import median

from prices.price_sources.makeup_mock import MakeupMockSource
from prices.price_sources.serper_shopping import SerperShoppingSource
# Exemplo: quando você tiver outras fontes, adicione aqui
# from prices.price_sources.serper_shopping import SerperShoppingSource

from prices.domain.catalog import classify_query, QueryProfile

logger = logging.getLogger(__name__)

# Lojas mais conhecidas para maquiagem / beleza
TRUSTED_STORES = {
    "sephora": 0.9,
    "panvel": 0.9,
    "droga raia": 0.9,
    "drogaria raia": 0.9,
    "drogasil": 0.9,
    "epoca cosmeticos": 0.9,
    "época cosmeticos": 0.9,
    "epoca cosméticos": 0.9,
    "magazine luiza": 0.9,
    "magalu": 0.9,
    "amazon": 0.9,
    "renner": 0.9,
    "cea": 0.9,
    "c&a": 0.9,
    "casas bahia": 0.9,
    "l'occitane": 0.9,
    "boticario": 0.9,
    "o boticário": 0.9,
}


class PriceAggregator:
    def __init__(self) -> None:
        self.sources = [
            # MakeupMockSource(),
            # Quando estiver usando Serper, por exemplo:
            SerperShoppingSource(),
        ]

    # ------------- Utils básicos -------------

    def _tokenize(self, text: str) -> List[str]:
        text = (text or "").lower()
        return [t for t in text.split() if t]

    def _normalize_title(self, title: str) -> str:
        return (title or "").lower().strip()

    # ------------- Relevância por texto -------------

    def _relevance_score(self, profile: QueryProfile, title: str) -> float:
        """
        Hoje deixamos simples: contar tokens do query que aparecem no título.
        Podemos evoluir depois com regras pra marca, categoria etc.
        """
        if not title:
            return 0.0

        title_l = self._normalize_title(title)
        tokens = profile.tokens  # vindo do classify_query()

        if not tokens:
            base = 1.0
        else:
            hits = sum(1 for token in tokens if token in title_l)
            base = hits / len(tokens)

        # leve bônus se começa com o primeiro token
        first_token = tokens[0] if tokens else ""
        if first_token and title_l.startswith(first_token):
            base += 0.1

        return base

    # ------------- Confiança por loja -------------

    def _store_factor(self, store_name: str) -> float:
        """
        Fator <= 1.0. Lojas “grandes” ganham fator 0.9 (ou semelhante),
        o que efetivamente “barateia” um pouco o preço na comparação.
        """
        name = (store_name or "").lower()
        for key, factor in TRUSTED_STORES.items():
            if key in name:
                return factor
        return 1.0  # loja desconhecida: sem desconto

    def _effective_price(self, item: Dict[str, Any]) -> float:
        """
        Preço ajustado pela confiança da loja.
        Se não tiver preço, devolve um número grande pra não ser escolhida.
        """
        price = item.get("price")
        if not isinstance(price, (int, float)):
            return 10**9  # muito grande, nunca será a menor

        store_factor = self._store_factor(item.get("store", ""))
        effective = price * store_factor
        item["store_trust_factor"] = store_factor
        item["effective_price"] = effective
        return effective

    # ------------- Filtro de outlier de preço -------------

    def _mark_price_outliers(self, results: List[Dict[str, Any]]) -> None:
        """
        Marca cada item com `price_outlier: True/False` usando a mediana.
        Outliers muito abaixo/acima da mediana são ignorados na escolha de 'best'.
        """
        prices = [
            r["price"]
            for r in results
            if isinstance(r.get("price"), (int, float))
        ]

        if len(prices) < 5:
            # Muito pouca amostra: não marca outlier
            for r in results:
                r["price_outlier"] = False
            return

        med = median(prices)
        LOW_FACTOR = 0.4   # abaixo de 40% da mediana => suspeito (baixo demais)
        HIGH_FACTOR = 2.5  # acima de 250% da mediana => suspeito (alto demais)

        logger.info("Mediana de preços: %.2f", med)

        for r in results:
            p = r.get("price")
            if not isinstance(p, (int, float)):
                r["price_outlier"] = False
                continue

            if p < LOW_FACTOR * med or p > HIGH_FACTOR * med:
                r["price_outlier"] = True
            else:
                r["price_outlier"] = False

    # ------------- Busca agregada -------------

    def search_all(self, query: str) -> Dict[str, Any]:
        profile: QueryProfile = classify_query(query)

        all_results: List[Dict[str, Any]] = []
        for source in self.sources:
            try:
                results = source.search(query)
                logger.info("[%s] retornou %d resultados", source.name, len(results))
                all_results.extend(results)
            except Exception:
                logger.exception("Erro ao buscar em %s", source.name)

        # Se nada voltou de nenhuma fonte
        if not all_results:
            return {
                "query": query,
                "results": [],
                "best": None,
            }

        # Calcula relevância textual
        for item in all_results:
            title = item.get("title", "")
            score = self._relevance_score(profile, title)
            item["relevance_score"] = score
            # por padrão, todo mundo é "relevante" até termos regras melhores
            item["relevant"] = score >= 0.2

        # Filtra por relevância mínima
        relevant_results = [r for r in all_results if r.get("relevant")]
        if not relevant_results:
            relevant_results = all_results

        # Marca outliers de preço dentro do conjunto relevante
        self._mark_price_outliers(relevant_results)

        # Candidatos para best: relevantes e não outlier
        candidates = [r for r in relevant_results if not r.get("price_outlier")]
        if not candidates:
            # Se todos forem outlier por algum motivo, volta pro conjunto relevante
            candidates = relevant_results

        # Escolhe melhor oferta pelo preço efetivo (preço * fator de confiança da loja)
        best = min(candidates, key=self._effective_price)

        logger.info(
            "Best escolhido: %s (preço=%.2f, efetivo=%.2f, outlier=%s)",
            best.get("title"),
            best.get("price"),
            best.get("effective_price"),
            best.get("price_outlier"),
        )

        # Ordena todos os resultados por relevância desc, depois preço asc
        all_results_sorted = sorted(
            all_results,
            key=lambda x: (-x.get("relevance_score", 0), x.get("price") or 10**9),
        )

        return {
            "query": query,
            "results": all_results_sorted,
            "best": best,
        }

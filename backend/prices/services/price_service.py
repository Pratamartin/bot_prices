from typing import Dict, Any, List

from prices.price_sources.mercado_livre import MercadoLivreAPISource
# Futuro: quando tiver APIs oficiais ou scrapers estáveis, você reativa:
# from prices.price_sources.kabum import KabumSource
# from prices.price_sources.magazine_luiza import MagazineLuizaSource

# Aqui você vai adicionando novas fontes
SOURCES = [
    MercadoLivreAPISource(),
    # KabumSource(),
    # MagazineLuizaSource(),
]


def list_mercado_livre_products(query: str) -> Dict[str, Any]:
    """
    Função simples só pra testar a integração com o Mercado Livre via API.
    NÃO compara preço, só retorna os produtos dessa fonte.
    """
    source = MercadoLivreAPISource()
    print(f"Buscando em {source.name}...")

    try:
        results = source.search(query)
        print(f"  Encontrados {len(results)} resultados.")
    except Exception as e:
        print(f"[{source.name}] erro ao buscar: {e}")
        results = []

    return {
        "query": query,
        "results": results,
    }


def compare_prices(query: str) -> Dict[str, Any]:
    """
    Versão “real”: chama todas as fontes configuradas em SOURCES
    (por enquanto só Mercado Livre API) e agrega os resultados.
    """
    all_results: List[Dict[str, Any]] = []

    for source in SOURCES:
        print(f"Buscando em {source.name}...")
        try:
            results = source.search(query)
            print(f"  Encontrados {len(results)} resultados.")
            all_results.extend(results)
        except Exception as e:
            # Em prod, ideal: usar logging estruturado
            print(f"[{source.name}] erro ao buscar: {e}")

    if not all_results:
        return {"query": query, "results": [], "best": None}

    # Espera que cada result tenha um campo "price" numérico
    best = min(all_results, key=lambda x: x["price"])

    return {
        "query": query,
        "results": all_results,
        "best": best,
    }


def compare_prices_mock(query: str) -> Dict[str, Any]:
    """
    Função mock pra testes rápidos sem chamar API nenhuma.
    """
    results: List[Dict[str, Any]] = [
        {
            "store": "Loja Fictícia A",
            "title": f"{query} - Versão Básica",
            "price": 3999.90,
            "url": "https://exemplo.com/produto-basico",
        },
        {
            "store": "Loja Fictícia B",
            "title": f"{query} - Versão Intermediária",
            "price": 3799.00,
            "url": "https://exemplo.com/produto-intermediario",
        },
    ]

    best = min(results, key=lambda x: x["price"])

    return {
        "query": query,
        "results": results,
        "best": best,
    }

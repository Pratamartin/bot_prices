# telegram_app/formatters.py
from typing import Dict, Any, List


def _format_currency(value: float, currency: str = "BRL") -> str:
    if currency == "BRL":
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{currency} {value:.2f}"


def format_price_response(result: Dict[str, Any], max_offers: int = 3) -> str:
    query = (result.get("query") or "").strip()
    best = result.get("best")
    offers: List[Dict[str, Any]] = result.get("results") or []

    if not offers and not best:
        return f"❌ Não encontrei ofertas para **{query or 'o produto informado'}**."

    # se por algum motivo best não estiver em offers, adiciona
    if best and best not in offers:
        offers = [best] + offers

    # filtra relevantes, se houver
    relevant_offers = [o for o in offers if o.get("relevant")]
    if not relevant_offers:
        relevant_offers = offers

    # coloca o best no topo da lista ordenada
    if best and best in relevant_offers:
        sorted_offers = [best] + [o for o in relevant_offers if o is not best]
    elif best:
        sorted_offers = [best] + relevant_offers
    else:
        sorted_offers = relevant_offers

    top_offers = sorted_offers[:max_offers]

    header_lines: List[str] = [f"🔍 Ofertas para **{query}**"]

    # --------- Bloco da melhor oferta ---------
    if best:
        best_store_name = best.get("store", "Loja").split("(")[0].strip()
        best_price = _format_currency(best["price"], best.get("currency", "BRL"))

        header_lines.append("")
        header_lines.append("💰 Melhor oferta encontrada:")
        header_lines.append(
            f"➡️ **{best_store_name}** — {best_price}\n"
            f"`{best.get('title', 'Produto')}`"
        )
        if best.get("url"):
            header_lines.append(best["url"])

    # --------- Bloco de outras ofertas ---------
    body_lines: List[str] = []

    # filtra top_offers removendo o best, pra não repetir
    other_offers = [
        o for o in top_offers
        if not (best and o is best)
    ]

    if other_offers:
        body_lines.append("")
        body_lines.append("📊 Outras ofertas:")
        for offer in other_offers:
            price_str = _format_currency(offer["price"], offer.get("currency", "BRL"))
            title = offer.get("title", "Produto")
            url = offer.get("url") or ""

            # pega o nome da loja certo pra CADA oferta,
            # não reaproveita o do best
            offer_store_name = offer.get("store", "Loja").split("(")[0].strip()

            line = f"• **{offer_store_name}** — {price_str}\n  `{title}`"
            if url:
                line += f"\n  {url}"
            body_lines.append(line)

    body_lines.append("")
    body_lines.append(
        "_Obs: formas de pagamento e parcelamento dependem da loja; "
        "verifique no link da oferta._"
    )

    return "\n".join(header_lines + body_lines)
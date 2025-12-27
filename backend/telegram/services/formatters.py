from typing import Any, Dict, List, Optional
import html

from prices.services.shortlinks import create_offer_shortlink


def _format_currency(value: Any, currency: str = "BRL") -> str:
    try:
        v = float(value)
    except Exception:
        return "—"
    if currency.upper() == "BRL":
        # Formato simples BR
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{v:,.2f} {currency}"


def _dedupe_by_key(offers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicados usando (store + title + price) como chave.
    """
    seen = set()
    out = []
    for o in offers:
        key = (
            str(o.get("store") or "").strip().lower(),
            str(o.get("title") or "").strip().lower(),
            str(o.get("price") or "").strip(),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(o)
    return out


def _same_offer(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    if not a or not b:
        return False
    return (
        (a.get("store") or "").strip().lower() == (b.get("store") or "").strip().lower()
        and (a.get("title") or "").strip().lower() == (b.get("title") or "").strip().lower()
        and str(a.get("price") or "") == str(b.get("price") or "")
    )


def format_price_response_html(
    result: Dict[str, Any],
    max_other_offers: int = 2,
    telegram_user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
) -> str:
    """
    Retorna mensagem em HTML (parse_mode="HTML") com:
    - Best separado
    - Outras ofertas sem duplicar best
    - Links curtos /r/<id>/ ao invés de google.com/search
    """
    query = (result.get("query") or "").strip()
    offers: List[Dict[str, Any]] = result.get("results") or []
    best: Optional[Dict[str, Any]] = result.get("best")

    if not offers:
        q = html.escape(query) if query else "o produto informado"
        return f"❌ Não encontrei ofertas para <b>{q}</b>."

    # Se você já marca relevant, prioriza; senão usa tudo
    relevant = [o for o in offers if o.get("relevant")]
    if not relevant:
        relevant = offers

    relevant = _dedupe_by_key(relevant)

    # Ordena por preço (e opcionalmente por relevance_score)
    # Mantém simples: pega candidatos relevantes ordenados por preço
    def price_key(o: Dict[str, Any]) -> float:
        try:
            return float(o.get("price"))
        except Exception:
            return 1e18

    relevant_sorted = sorted(relevant, key=price_key)

    # Se best veio, tenta garantir que ele existe nos relevantes
    if best:
        # normaliza best para apontar para um item equivalente de relevant_sorted se possível
        best_match = None
        for o in relevant_sorted:
            if _same_offer(o, best):
                best_match = o
                break
        if best_match:
            best = best_match
        else:
            # se best não está nos relevantes, usa o best mesmo, mas ele pode não estar em sorted
            pass
    else:
        best = relevant_sorted[0] if relevant_sorted else None

    # Monta “outras ofertas” removendo best
    others = []
    for o in relevant_sorted:
        if best and _same_offer(o, best):
            continue
        others.append(o)
        if len(others) >= max_other_offers:
            break

    # Header
    q = html.escape(query) if query else "produto"
    lines: List[str] = [f"🔍 Ofertas para <b>{q}</b>"]

    # Best
    if best:
        store = html.escape((best.get("store") or "Loja").split("(")[0].strip())
        title = html.escape(best.get("title") or "Produto")
        price_str = _format_currency(best.get("price"), best.get("currency", "BRL"))

        # shortlink
        short = create_offer_shortlink(best, telegram_user_id=telegram_user_id, chat_id=chat_id)

        lines += [
            "",
            "💰 <b>Melhor oferta encontrada:</b>",
            f"➡️ <b>{store}</b> — {price_str}",
            f"{title}",
            f"<a href=\"{html.escape(short)}\">Abrir oferta</a>",
        ]

    # Others
    if others:
        lines += ["", "📊 <b>Outras ofertas:</b>"]
        for o in others:
            store = html.escape((o.get("store") or "Loja").split("(")[0].strip())
            title = html.escape(o.get("title") or "Produto")
            price_str = _format_currency(o.get("price"), o.get("currency", "BRL"))
            short = create_offer_shortlink(o, telegram_user_id=telegram_user_id, chat_id=chat_id)

            lines += [
                f"• <b>{store}</b> — {price_str}",
                f"  {title}",
                f"  <a href=\"{html.escape(short)}\">Abrir oferta</a>",
            ]

    lines += [
        "",
        "<i>Obs: formas de pagamento e parcelamento dependem da loja; verifique no link da oferta.</i>",
    ]

    # Proteção simples contra mensagem gigante
    msg = "\n".join(lines)
    if len(msg) > 3800:
        msg = msg[:3800] + "\n…"

    return msg

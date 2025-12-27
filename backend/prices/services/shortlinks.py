from typing import Any, Dict
from django.conf import settings
from prices.models import OfferLink


def create_offer_shortlink(
    offer: Dict[str, Any],
    telegram_user_id: int | None = None,
    chat_id: int | None = None,
) -> str:
    """
    Persiste a oferta e retorna um link curto /r/<id>/.
    Opcionalmente inclui user/chat na querystring para analytics.
    """
    obj = OfferLink.objects.create(
        source=str(offer.get("source") or ""),
        store=str(offer.get("store") or ""),
        title=str(offer.get("title") or ""),
        price=offer.get("price"),
        currency=str(offer.get("currency") or "BRL"),
        target_url=str(offer.get("url") or ""),
    )

    base = settings.PUBLIC_BASE_URL.rstrip("/")
    url = f"{base}/r/{obj.id}/"

    qs = []
    if telegram_user_id is not None:
        qs.append(f"u={telegram_user_id}")
    if chat_id is not None:
        qs.append(f"c={chat_id}")
    if qs:
        url += "?" + "&".join(qs)

    return url

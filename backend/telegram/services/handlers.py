import logging
import re
from typing import Any, Dict

from prices.services.price_agregator import PriceAggregator
from .bot_client import safe_send_message
from .formatters import format_price_response

logger = logging.getLogger(__name__)


def extract_query_from_text(text: str) -> str:
    t = (text or "").strip()

    m = re.match(r"/ofertas\s+(.+)", t, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip(" ?!.")

    m = re.search(r"ofertas\s+(do|da|de)\s+(.+)", t, flags=re.IGNORECASE)
    if m:
        return m.group(2).strip(" ?!.")

    return t


def handle_update(update: Dict[str, Any]) -> None:
    message = update.get("message") or update.get("edited_message")
    if not message:
        logger.info("Update sem message: %s", update)
        return

    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = message.get("text") or ""

    if chat_id is None:
        logger.info("Message sem chat_id: %s", message)
        return

    if text.startswith("/start"):
        safe_send_message(
            chat_id,
            "Oi! Eu sou o PriceBot 💸\n\n"
            "Me mande algo como:\n"
            "`Quais são as ofertas do iPhone 13 128GB?`\n\n"
            "ou\n"
            "`/ofertas notebook gamer`",
        )
        return

    query = extract_query_from_text(text)
    if not query:
        safe_send_message(
            chat_id,
            "Não entendi o produto 😅\n"
            "Tenta algo como:\n"
            "`Quais são as ofertas do iPhone 13 128GB?`",
        )
        return

    logger.info("Consulta do bot: %s (query: %s)", text, query)

    aggregator = PriceAggregator()
    result = aggregator.search_all(query)

    message_text = format_price_response(result)
    safe_send_message(chat_id, message_text)

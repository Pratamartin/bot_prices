import logging
import re
from typing import Any, Dict

from prices.services.price_agregator import PriceAggregator
from .bot_client import safe_send_message, safe_answer_callback_query 
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
    """
    Decide se o update é mensagem normal ou clique em botão (callback_query)
    e delega para o handler certo.
    """

    callback = update.get("callback_query")
    if callback:
        handle_callback_query(callback)
        return

    message = update.get("message") or update.get("edited_message")
    if not message:
        logger.info("Update sem message nem callback_query: %s", update)
        return

    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = message.get("text") or ""

    if chat_id is None:
        logger.info("Message sem chat_id: %s", message)
        return

    if text.startswith("/start"):
        send_start_message_with_categories(chat_id)
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

    send_followup_question(chat_id)


def send_followup_question(chat_id: int) -> None:
    """
    Envia uma mensagem com botões perguntando se o usuário quer mais alguma coisa.
    """
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "🔎 Nova busca", "callback_data": "action:new_search"},
                {"text": "❌ Encerrar", "callback_data": "action:close"},
            ]
        ]
    }

    text = (
        "Posso te ajudar com mais alguma coisa? 🙂\n\n"
        "Você pode:\n"
        "• Fazer uma *nova busca* clicando em \"Nova busca\"\n"
        "• Ou simplesmente digitar o nome de outro produto"
    )

    safe_send_message(
        chat_id,
        text,
        reply_markup=reply_markup,
        
    )



def send_start_message_with_categories(chat_id: int) -> None:
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "🎮 Consoles", "callback_data": "cat:console"},
                {"text": "📱 Celulares", "callback_data": "cat:phone"},
                {"text": "🛍️ Outra", "callback_data": "cat:other"},
            ],
        ]
    }

    text = (
        "Olá! Eu sou o PriceBot 💸\n\n"
        "Primeiro, escolha uma categoria:\n"
        "• Consoles (PS5, Xbox, etc.)\n"
        "• Celulares (iPhone, Galaxy, etc.)\n\n"
        "• Outra categoria qualquer (roupas, eletrodomésticos, etc.)\n\n"
        "Depois eu te peço o modelo e mostro as melhores ofertas 😉"
    )

    safe_send_message(
        chat_id,
        text,
        reply_markup=reply_markup,
    )



def handle_callback_query(callback: Dict[str, Any]) -> None:
    callback_id = callback.get("id")
    data = callback.get("data") or ""
    message = callback.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")

    logger.info("Callback recebido: %s", data)

    if callback_id:
        safe_answer_callback_query(callback_id)

    if chat_id is None:
        return

    if data.startswith("cat:"):
        category = data.split(":", 1)[1]

        if category == "console":
            text = (
                "Beleza, vamos procurar *consoles* 🎮\n\n"
                "Agora me manda o modelo que você quer, por exemplo:\n"
                "• `ps5`\n"
                "• `playstation 5 slim`\n"
                "• `xbox series x`"
            )
        elif category == "phone":
            text = (
                "Show! Vamos procurar *celulares* 📱\n\n"
                "Agora me manda o modelo, por exemplo:\n"
                "• `iphone 13 128gb`\n"
                "• `galaxy s23`\n"
                "• `redmi note 13`"
            )
        elif category == "other":
            text = (
                "Ok, categoria outra selecionada 🛍️\n\n"
                "Me manda o produto que você quer buscar, por exemplo:\n"
                "• tênis nike air max\n"
                "• geladeira frost free\n"
                "• smart tv 50 polegadas"
            )
        else:
            text = (
                "Categoria selecionada 👍\n"
                "Agora me manda o produto que você quer buscar:"
            )

        safe_send_message(chat_id, text)
        return

    if data == "action:new_search":
        safe_send_message(
            chat_id,
            "Beleza! Me manda o nome do próximo produto que você quer pesquisar 🕵️‍♂️",
        )
        return

    if data == "action:close":
        safe_send_message(
            chat_id,
            "Fechado! Se precisar, é só mandar outra mensagem ou usar /start 😄",
        )
        return



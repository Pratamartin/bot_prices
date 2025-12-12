import logging
import re
import os
from typing import Any, Dict

from prices.domain.makeup_terms import is_makeup_query
from prices.services.price_agregator import PriceAggregator
from .bot_client import safe_send_message, safe_answer_callback_query 
from .formatters import format_price_response

from telegram.models import SearchLog

GLOBAL_CHAT_ID = os.environ.get("PRICEBOT_GLOBAL_CHAT_ID")
# Hardcoded bot id (aceita ser hardcoded conforme pedido)
BOT_ID = int(os.environ.get("TELEGRAM_BOT_ID", "8176839555"))

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
    # trata updates do tipo my_chat_member (quando o bot é adicionado/alterado em um chat)
    my_chat_member = update.get("my_chat_member")
    if my_chat_member:
        chat = my_chat_member.get("chat") or {}
        new = my_chat_member.get("new_chat_member") or {}
        user = new.get("user") or {}
        # se for o nosso bot, printa o grupo
        if user.get("is_bot") and user.get("id") == BOT_ID:
            print(f"Bot adicionado ao grupo (my_chat_member): id={chat.get('id')}, title={chat.get('title')}")
            logger.info("Bot adicionado via my_chat_member: %s (%s)", chat.get("title"), chat.get("id"))
        return

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

    # Verifica se há novos membros na mensagem (quando o bot é adicionado)
    new_members = message.get("new_chat_members") or []
    for m in new_members:
        if m.get("is_bot") and m.get("id") == BOT_ID:
            print(f"Bot adicionado ao grupo (new_chat_members): id={chat.get('id')}, title={chat.get('title')}")
            logger.info("Bot adicionado via new_chat_members: %s (%s)", chat.get("title"), chat.get("id"))

    if chat_id is None:
        logger.info("Message sem chat_id: %s", message)
        return

    if text.startswith("/start"):
        send_start_message_with_categories(chat_id)
        return

    query = extract_query_from_text(text)
    
    if not is_makeup_query(query):
        safe_send_message(
            chat_id,
            "Este bot funciona somente com produtos de maquiagem 💄\n"
            "Tente algo como:\n"
            "• gloss liphoney\n"
            "• base ruby rose\n"
            "• paleta bruna tavares"
    )
        return
    
    if not query:
        safe_send_message(
            chat_id,
            "Não entendi o produto 😅\n"
            "Tenta algo como:\n"
            "Quais são as ofertas de base matte para pele oleosa?",
        )
        return
    

    logger.info("Consulta do bot: %s (query: %s)", text, query)

    aggregator = PriceAggregator()
    result = aggregator.search_all(query)

    message_text = format_price_response(result)
    safe_send_message(chat_id, message_text)

    # pergunta se quer nova busca / encerrar
    send_followup_question(chat_id)

    # ---- LOG NO BANCO ----
    best = result.get("best")

    try:
        SearchLog.objects.create(
            user_id=message["from"]["id"],
            username=message["from"].get("username"),
            query_raw=text,
            query_clean=query,
            best_store=best.get("store") if best else None,
            best_title=best.get("title") if best else None,
            best_price=best.get("price") if best else None,
            best_url=best.get("url") if best else None,
        )
    except Exception:
        logger.exception("Erro ao salvar SearchLog")

    # ---- BROADCAST ANÔNIMO PRO GRUPO GLOBAL ----
    if GLOBAL_CHAT_ID and best:
        try:
            # tentativa de converter o ID
            global_chat_id = int(GLOBAL_CHAT_ID)
        except (TypeError, ValueError):
            logger.warning("PRICEBOT_GLOBAL_CHAT_ID inválido: %s", GLOBAL_CHAT_ID)
            return

        store_name = (best.get("store") or "Loja").split("(")[0].strip()
        price = best.get("price")
        title = best.get("title") or "Produto"
        url = best.get("url") or ""

        # formata preço de forma segura
        if isinstance(price, (int, float)):
            price_str = f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            price_str = "preço indisponível"

        group_msg_lines = [
            "🛍️ Nova busca no bot de make:",
            f"“{query}”",
            "",
            "💰 Melhor oferta encontrada:",
            f"{store_name} — {price_str}",
            title,
        ]
        if url:
            group_msg_lines.append(url)

        group_msg = "\n".join(group_msg_lines)

        try:
            safe_send_message(global_chat_id, group_msg)
        except Exception:
            logger.exception("Erro ao enviar mensagem para grupo global")



def _broadcast_best_offer_to_global(query: str, best: Dict[str, Any]) -> None:
    """Envia a melhor oferta para o grupo/canal global, de forma anônima."""
    if not GLOBAL_CHAT_ID:
        return

    try:
        chat_id = int(GLOBAL_CHAT_ID)
    except ValueError:
        logger.warning("PRICEBOT_GLOBAL_CHAT_ID inválido: %s", GLOBAL_CHAT_ID)
        return

    store_name = (best.get("store") or "Loja").split("(")[0].strip()
    price = best.get("price")
    currency = best.get("currency", "BRL")
    title = best.get("title") or "Produto"
    url = best.get("url") or ""

    price_str = format_price_response(price, currency)

    lines = [
        "💄 Nova oferta encontrada pelo bot de make:",
        "",
        f"🔎 Busca: {query}",
        "",
        "💰 Melhor oferta:",
        f"{store_name} — {price_str}",
        title,
    ]
    if url:
        lines.append(url)

    text = "\n".join(lines)
    safe_send_message(chat_id, text)  # sem parse_mode pra evitar erro de Markdown

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
                {"text": "💄 Rosto",    "callback_data": "cat:face"},
                {"text": "👁️ Olhos",   "callback_data": "cat:eyes"},
            ],
            [
                {"text": "💋 Lábios",   "callback_data": "cat:lips"},
                {"text": "🧴 Skincare", "callback_data": "cat:skincare"},
            ],
            [
                {"text": "🛍️ Tudo",    "callback_data": "cat:all"},
            ],
        ]
    }

    text = (
        "Oi! Eu sou o MakeOfertas Bot 💄\n\n"
        "Te ajudo a achar ofertas de maquiagem e beleza em grandes lojas online.\n\n"
        "Você pode escolher uma categoria aqui embaixo ou simplesmente me dizer o que procura, "
        "por exemplo:\n"
        "• base para pele oleosa\n"
        "• batom vermelho matte\n"
        "• máscara de cílios à prova d’água\n"
        "• paleta de sombra neutra\n"
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

    # -------- categorias de maquiagem --------
    if data.startswith("cat:"):
        category = data.split(":", 1)[1]

        if category == "face":
            text = (
                "Beleza! Vamos procurar produtos para *rosto* 💄\n\n"
                "Me manda o que você quer, por exemplo:\n"
                "• base matte para pele oleosa\n"
                "• corretivo alta cobertura\n"
                "• pó compacto translúcido\n"
            )
        elif category == "eyes":
            text = (
                "Show! Vamos focar em *olhos* 👁️\n\n"
                "Exemplos do que você pode pedir:\n"
                "• máscara de cílios à prova d’água\n"
                "• delineador líquido preto\n"
                "• paleta de sombras neutra\n"
            )
        elif category == "lips":
            text = (
                "Ok, vamos de *lábios* 💋\n\n"
                "Exemplos:\n"
                "• batom vermelho matte\n"
                "• gloss labial incolor\n"
                "• lip tint rosado\n"
            )
        elif category == "skincare":
            text = (
                "Bora ver *skincare* 🧴\n\n"
                "Você pode pedir coisas como:\n"
                "• hidratante facial pele oleosa\n"
                "• protetor solar rosto fps 50\n"
                "• sérum vitamina C\n"
            )
        else:  # "all" ou qualquer outra coisa
            text = (
                "Categoria geral selecionada 🛍️\n\n"
                "Me conta o que você está procurando, por exemplo:\n"
                "• kit maquiagem básica\n"
                "• necessaire\n"
                "• espelho de maquiagem com luz\n"
            )

        # aqui eu usaria sem Markdown pra não dar erro; se quiser Markdown, tira os *...*
        safe_send_message(chat_id, text)
        return

    # -------- ações de follow-up (se você já tiver) --------
    if data == "action:new_search":
        safe_send_message(
            chat_id,
            "Beleza! Me manda o nome do próximo produto de maquiagem/beleza que você quer pesquisar 🕵️‍♀️",
        )
        return

    if data == "action:close":
        safe_send_message(
            chat_id,
            "Fechado! Se precisar, é só mandar outra mensagem ou usar /start 😄",
        )
        return



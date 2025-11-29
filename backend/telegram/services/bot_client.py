import os
import logging
import requests

logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


def safe_send_message(chat_id: int, text: str, reply_markup: dict | None = None, parse_mode: str | None = None) -> None:
    payload: dict = {
        "chat_id": chat_id,
        "text": text,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        resp = requests.post(f"{TELEGRAM_API_BASE}/sendMessage", json=payload, timeout=10)
        if resp.status_code != 200:
            logger.warning("Erro ao enviar mensagem para %s: %s", chat_id, resp.text)
    except Exception:
        logger.exception("Falha ao enviar mensagem para %s", chat_id)


def safe_answer_callback_query(callback_query_id: str, text: str | None = None) -> None:
    payload: dict = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text

    try:
        resp = requests.post(f"{TELEGRAM_API_BASE}/answerCallbackQuery", json=payload, timeout=10)
        if resp.status_code != 200:
            logger.warning("Erro ao responder callback_query %s: %s", callback_query_id, resp.text)
    except Exception:
        logger.exception("Falha ao responder callback_query %s", callback_query_id)

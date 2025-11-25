import os
import logging
from typing import Any, Dict
import requests

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}" if TELEGRAM_BOT_TOKEN else None


def safe_send_message(chat_id: int, text: str, parse_mode: str | None = "Markdown") -> Dict[str, Any] | None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_API_BASE:
        logger.error("TELEGRAM_BOT_TOKEN não configurado; não é possível enviar mensagem.")
        return None

    url = f"{TELEGRAM_API_BASE}/sendMessage"
    payload: Dict[str, Any] = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            logger.error("Erro ao enviar mensagem pro Telegram: %s - %s", resp.status_code, resp.text)
            return None
        return resp.json()
    except requests.RequestException as e:
        logger.exception("Erro de rede ao enviar mensagem pro Telegram: %s", e)
        return None

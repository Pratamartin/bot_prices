from django.shortcuts import render

# Create your views here.
import json
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .services.handlers import handle_update

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def telegram_webhook(request):
    try:
        body = request.body.decode("utf-8")
        update = json.loads(body)
    except Exception as e:
        logger.exception("Erro ao ler update do Telegram: %s", e)
        return HttpResponse(status=400)

    logger.info("Update recebido do Telegram: %s", update)
    handle_update(update)
    return HttpResponse(status=200)

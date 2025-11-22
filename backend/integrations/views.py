from django.shortcuts import render

import requests
from urllib.parse import urlencode
from datetime import timedelta

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.utils import timezone

from .models import MercadoLivreToken

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt


def ml_auth_start(request):
    """
    Inicia o fluxo OAuth do Mercado Livre.
    Redireciona o usuário para o login/autorização do ML.
    """
    params = {
        "response_type": "code",
        "client_id": settings.ML_CLIENT_ID,
        "redirect_uri": settings.ML_REDIRECT_URI,
    }
    url = f"https://auth.mercadolivre.com.br/authorization?{urlencode(params)}"
    return redirect(url)


def ml_auth_callback(request):
    """
    Recebe o 'code' do ML e troca por access_token + refresh_token.
    Salva no banco.
    """
    code = request.GET.get("code")
    if not code:
        return HttpResponseBadRequest("Missing code")

    token_url = "https://api.mercadolibre.com/oauth/token"

    data = {
        "grant_type": "authorization_code",
        "client_id": settings.ML_CLIENT_ID,
        "client_secret": settings.ML_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.ML_REDIRECT_URI,
    }

    resp = requests.post(token_url, data=data, timeout=15)
    if resp.status_code != 200:
        return HttpResponse(
            f"Erro ao obter token: {resp.status_code} {resp.text}",
            status=resp.status_code,
        )

    payload = resp.json()
    access_token = payload["access_token"]
    refresh_token = payload["refresh_token"]
    expires_in = payload["expires_in"]  # segundos

    expires_at = timezone.now() + timedelta(seconds=expires_in)

    # mantém só 1 registro (token global)
    MercadoLivreToken.objects.all().delete()
    MercadoLivreToken.objects.create(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
    )

    return HttpResponse("Token do Mercado Livre salvo com sucesso. Pode fechar esta aba.")



@csrf_exempt  # Mercado Livre não manda CSRF token
@api_view(["POST"])
def ml_notifications(request):
    """
    Webhook de notificações do Mercado Livre.
    Aqui o ML vai enviar eventos de pedidos, produtos, etc.
    """
    print("[ML NOTIFICATION] data:", request.data)
    # depois você trata por topic, resource, etc.
    return Response({"status": "received"})
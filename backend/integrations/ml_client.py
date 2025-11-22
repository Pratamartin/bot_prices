import requests
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import MercadoLivreToken


def get_ml_token() -> str:
    """
    Retorna um access_token válido.
    Se estiver expirado (ou perto de expirar), tenta renovar usando o refresh_token.
    """
    token_obj = MercadoLivreToken.objects.first()
    if not token_obj:
        raise RuntimeError(
            "Nenhum token do Mercado Livre configurado. "
            "Acesse /ml/auth/start para autorizar o aplicativo."
        )

    # se já expirou ou vai expirar em menos de 1 min
    if token_obj.expires_at <= timezone.now() + timedelta(minutes=1):
        _refresh_ml_token(token_obj)

    return token_obj.access_token


def _refresh_ml_token(token_obj: MercadoLivreToken):
    url = "https://api.mercadolibre.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": settings.ML_CLIENT_ID,
        "client_secret": settings.ML_CLIENT_SECRET,
        "refresh_token": token_obj.refresh_token,
    }

    resp = requests.post(url, data=data, timeout=15)
    resp.raise_for_status()
    payload = resp.json()

    token_obj.access_token = payload["access_token"]
    token_obj.refresh_token = payload["refresh_token"]
    token_obj.expires_at = timezone.now() + timedelta(seconds=payload["expires_in"])
    token_obj.save()

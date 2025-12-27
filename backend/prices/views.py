from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from prices.services.price_agregator import PriceAggregator
from django.db.models import F
from django.http import Http404
from django.shortcuts import redirect
from django.views.decorators.http import require_GET

from .models import OfferLink, OfferClick


@require_GET
def search_prices(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"error": "missing_query", "message": "Parâmetro q é obrigatório"}, status=400)

    aggregator = PriceAggregator()
    result = aggregator.search_all(query)

    return JsonResponse(result, status=200)

@require_GET
def redirect_offer(request, offer_id: int):
    try:
        offer = OfferLink.objects.get(id=offer_id)
    except OfferLink.DoesNotExist:
        raise Http404("Offer not found")

    OfferLink.objects.filter(id=offer_id).update(clicks=F("clicks") + 1)

    OfferClick.objects.create(
        offer=offer,
        user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:512],
        referer=(request.META.get("HTTP_REFERER") or "")[:1024],
        # telegram ids: se você quiser passar por querystring depois (ex: ?u=123&c=456)
        telegram_user_id=request.GET.get("u") or None,
        chat_id=request.GET.get("c") or None,
    )

    return redirect(offer.target_url)
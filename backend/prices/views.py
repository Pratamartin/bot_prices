from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from prices.services.price_agregator import PriceAggregator



@require_GET
def search_prices(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"error": "missing_query", "message": "Parâmetro q é obrigatório"}, status=400)

    aggregator = PriceAggregator()
    result = aggregator.search_all(query)

    return JsonResponse(result, status=200)
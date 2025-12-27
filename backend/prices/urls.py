from django.urls import path, include
from .views import search_prices, redirect_offer
from . import views

urlpatterns = [
    path("prices/", search_prices, name="price-search"),
    path("r/<int:offer_id>/", redirect_offer, name="redirect_offer"),
]

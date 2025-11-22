from django.urls import path, include
from .views import search_prices
from . import views

urlpatterns = [
    path("prices/", search_prices, name="price-search"),
]

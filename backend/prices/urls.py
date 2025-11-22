from django.urls import path, include
from .views import search_prices
from . import views

urlpatterns = [
    path("prices/", search_prices, name="price-search"),    path("api/prices/ml/", views.ml_products_search, name="ml_products_search"),
]

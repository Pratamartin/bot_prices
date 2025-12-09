from django.db import models

class SearchLog(models.Model):
    user_id = models.BigIntegerField()  # telegram user id -> pegar na hora que iniciar o bot
    username = models.CharField(max_length=255, blank=True, null=True)
    query_raw = models.TextField()
    query_clean = models.TextField()
    best_store = models.CharField(max_length=255, blank=True, null=True)
    best_title = models.TextField(blank=True, null=True)
    best_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    best_url = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

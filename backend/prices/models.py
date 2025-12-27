from django.db import models

class OfferLink(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    # dados do resultado
    source = models.CharField(max_length=64, blank=True, default="")
    store = models.CharField(max_length=128, blank=True, default="")
    title = models.CharField(max_length=512, blank=True, default="")
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=8, blank=True, default="BRL")

    # destino real (no início: link do google shopping)
    target_url = models.URLField(max_length=2048)

    # rastreio simples
    clicks = models.PositiveIntegerField(default=0)

class OfferClick(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    offer = models.ForeignKey(OfferLink, on_delete=models.CASCADE, related_name="click_events")

    telegram_user_id = models.BigIntegerField(null=True, blank=True)
    chat_id = models.BigIntegerField(null=True, blank=True)

    user_agent = models.CharField(max_length=512, blank=True, default="")
    referer = models.CharField(max_length=1024, blank=True, default="")

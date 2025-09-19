from django.db import models
class Company(models.Model):
    ticker = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.ticker

class Subscription(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='subscriptions')
    discord_channel = models.CharField(max_length=200)  # channel id or name
    webhook = models.URLField(blank=True)  # optional: external webhook
    created_at = models.DateTimeField(auto_now_add=True)

class Alert(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='alerts')
    score = models.FloatField()
    summary = models.TextField(blank=True)
    payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

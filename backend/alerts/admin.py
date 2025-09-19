from django.contrib import admin
from .models import Company, Subscription, Alert
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('id','ticker','name','created_at')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id','company','discord_channel','slack_channel','jira_project','created_at')

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('id','company','score','delivered','created_at')

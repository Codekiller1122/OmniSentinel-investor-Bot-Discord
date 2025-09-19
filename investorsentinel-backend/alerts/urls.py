from django.urls import path
from . import views

urlpatterns = [
    path('companies/add/', views.add_company),
    path('companies/', views.list_companies),
    path('subscriptions/add/', views.subscribe_channel),
    path('subscriptions/', views.list_subscriptions),
    path('alerts/create/', views.create_alert),
    path('stream/sse/', views.sse_stream),
]

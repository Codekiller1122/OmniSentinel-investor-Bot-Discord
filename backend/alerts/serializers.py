from rest_framework import serializers
from .models import Company, Subscription, Alert
class CompanySerializer(serializers.ModelSerializer):
    class Meta: model = Company; fields = '__all__'
class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta: model = Subscription; fields = '__all__'
class AlertSerializer(serializers.ModelSerializer):
    class Meta: model = Alert; fields = '__all__'

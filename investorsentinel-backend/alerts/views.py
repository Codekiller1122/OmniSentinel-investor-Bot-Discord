import json, time, threading
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, StreamingHttpResponse
from rest_framework.decorators import api_view
from .models import Company, Subscription, Alert
from .serializers import CompanySerializer, SubscriptionSerializer, AlertSerializer

# simple endpoints to add/list companies and subscriptions
@api_view(['POST'])
def add_company(request):
    ticker = request.data.get('ticker')
    name = request.data.get('name','')
    if not ticker: return JsonResponse({'error':'ticker required'}, status=400)
    c, _ = Company.objects.get_or_create(ticker=ticker.upper(), defaults={'name':name})
    return JsonResponse(CompanySerializer(c).data)

@api_view(['GET'])
def list_companies(request):
    qs = Company.objects.all().order_by('-created_at')
    return JsonResponse(CompanySerializer(qs, many=True).data, safe=False)

@api_view(['POST'])
def subscribe_channel(request):
    ticker = request.data.get('ticker')
    channel = request.data.get('channel')
    if not ticker or not channel: return JsonResponse({'error':'ticker and channel required'}, status=400)
    c = get_object_or_404(Company, ticker=ticker.upper())
    s = Subscription.objects.create(company=c, discord_channel=channel)
    return JsonResponse(SubscriptionSerializer(s).data)

@api_view(['GET'])
def list_subscriptions(request):
    qs = Subscription.objects.all().order_by('-created_at')
    return JsonResponse(SubscriptionSerializer(qs, many=True).data, safe=False)

# Endpoint for external systems to POST an alert (e.g., your LeadFinder or Stock scanner)
@api_view(['POST'])
def create_alert(request):
    ticker = request.data.get('ticker')
    score = float(request.data.get('score',0))
    summary = request.data.get('summary','')
    payload = request.data.get('payload', {})
    if not ticker: return JsonResponse({'error':'ticker required'}, status=400)
    c, _ = Company.objects.get_or_create(ticker=ticker.upper())
    a = Alert.objects.create(company=c, score=score, summary=summary, payload=payload)
    # optionally: deliver to webhooks (not implemented) - subscribers include Discord bot
    return JsonResponse(AlertSerializer(a).data)

# SSE stream for bots to listen to
@api_view(['GET'])
def sse_stream(request):
    def event_stream():
        last_id = None
        while True:
            try:
                latest = Alert.objects.order_by('-created_at').first()
                if latest and (str(latest.id) != str(last_id)):
                    last_id = latest.id
                    data = {'id': latest.id, 'ticker': latest.company.ticker, 'score': latest.score, 'summary': latest.summary, 'time': latest.created_at.isoformat()}
                    yield f'data: {json.dumps(data)}\n\n'
                time.sleep(2)
            except GeneratorExit:
                break
            except Exception as e:
                yield f'data: {json.dumps({"error": str(e)})}\n\n'
                time.sleep(5)
    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

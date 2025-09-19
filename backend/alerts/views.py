import json, time, threading, base64
import requests
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, StreamingHttpResponse
from rest_framework.decorators import api_view
from django.conf import settings
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
    channel = request.data.get('channel')      # discord channel id
    slack_channel = request.data.get('slack') # slack channel or webhook url
    jira_project = request.data.get('jira')   # jira project key
    if not ticker or not channel: return JsonResponse({'error':'ticker and channel required'}, status=400)
    c = get_object_or_404(Company, ticker=ticker.upper())
    s = Subscription.objects.create(company=c, discord_channel=str(channel), slack_channel=slack_channel or '', jira_project=jira_project or '')
    return JsonResponse(SubscriptionSerializer(s).data)

@api_view(['GET'])
def list_subscriptions(request):
    qs = Subscription.objects.all().order_by('-created_at')
    return JsonResponse(SubscriptionSerializer(qs, many=True).data, safe=False)

# Endpoint for external systems to POST an alert (e.g., Stock LeadFinder AI)
@api_view(['POST'])
def create_alert(request):
    ticker = request.data.get('ticker')
    score = float(request.data.get('score',0))
    summary = request.data.get('summary','')
    payload = request.data.get('payload', {})
    if not ticker: return JsonResponse({'error':'ticker required'}, status=400)
    c, _ = Company.objects.get_or_create(ticker=ticker.upper())
    a = Alert.objects.create(company=c, score=score, summary=summary, payload=payload)
    # deliver to subscriptions asynchronously
    threading.Thread(target=deliver_alert, args=(a.id,)).start()
    return JsonResponse(AlertSerializer(a).data)

def deliver_alert(alert_id):
    try:
        a = Alert.objects.get(id=alert_id)
        subs = Subscription.objects.filter(company=a.company)
        for s in subs:
            # Discord delivery via bot reads SSE; here optionally call a webhook (not Discord bot)
            # Slack: use platform-wide webhook or per-subscription override
            slack_url = s.slack_channel or settings.SLACK_WEBHOOK_URL
            if slack_url:
                try:
                    payload = {'text': f'ALERT: {a.company.ticker} score={a.score}\n{a.summary[:800]}'}
                    requests.post(slack_url, json=payload, timeout=5)
                except Exception as e:
                    print('slack send error', e)
            # Jira: create an issue if project specified
            if s.jira_project and settings.JIRA_BASE and settings.JIRA_USER and settings.JIRA_API_TOKEN:
                try:
                    jira_url = settings.JIRA_BASE.rstrip('/') + '/rest/api/2/issue'
                    auth = (settings.JIRA_USER, settings.JIRA_API_TOKEN)
                    issue = {
                        'fields': {
                            'project': {'key': s.jira_project},
                            'summary': f'Alert: {a.company.ticker} sentiment spike ({a.score})',
                            'description': a.summary + '\n\nPayload:\n' + json.dumps(a.payload)[:3000],
                            'issuetype': {'name': 'Task'}
                        }
                    }
                    r = requests.post(jira_url, json=issue, auth=auth, timeout=5)
                    if r.status_code in (200,201):
                        print('jira created', r.json().get('key'))
                except Exception as e:
                    print('jira create error', e)
        a.delivered = True
        a.save()
    except Exception as e:
        print('deliver_alert error', e)

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

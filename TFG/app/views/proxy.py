from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import requests
import json

@csrf_exempt 
def proxy_to_agent(request):
    if not settings.AI_AGENT_INTERNAL_URL:
        return JsonResponse({'error': 'AI Agent URL not configured'}, status=500)
    
    proxy_headers = {
        'Content-Type': 'application/json'
    }

    agent_secret = getattr(settings, 'AGENT_SECRET_KEY', None)
    if agent_secret:
        proxy_headers['X-Agent-Secret'] = agent_secret

    try:
       
        response = requests.post(
            url=settings.AI_AGENT_INTERNAL_URL,
            json=json.loads(request.body),
            headers=proxy_headers,
            timeout=80 
        )

        
        return HttpResponse(
            content=response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type', 'application/json')
        )

    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'Proxy request failed: {e}'}, status=502) 
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
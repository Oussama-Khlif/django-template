from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from .models import Notification
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django.views import View
from django.utils.decorators import method_decorator
import json

def index(request):
    return render(request, 'index.html')

@login_required
def settings(request):
    user = request.user

    if request.method == "POST":
        try:
            sounds = request.POST.get('sounds', 'false').lower() == 'true'

            user.settings = {
                "sounds": sounds,
            }
            user.save()
            messages.success(request, _("Settings updated successfully."))
            return redirect('settings')
        except Exception:
            messages.error(request, _("An error occurred while saving your settings."))
            return redirect('settings')

    current_settings = user.settings or {}
    context = {
        "sounds": current_settings.get("sounds", False),
    }
    return render(request, 'settings.html', context)

def about(request):
    return render(request, 'about.html')

@login_required
def get_notifications(request):
    notifications_queryset = request.user.notifications.all()
    unread_count = notifications_queryset.count()  
    latest_notifications = notifications_queryset.order_by('-created_at')[:5]

    return JsonResponse({
        'notifications': [
            {
                'id': n.id,
                'message': n.message,
                'url': n.url,
                'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'type': getattr(n, 'type', 'system')  
            } 
            for n in latest_notifications
        ],
        'unread_count': unread_count 
    })

@login_required
def redirect_and_delete_notification(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)

    target_url = notification.url or '/'

    notification.delete()

    return redirect(target_url)

@login_required
def delete_notifications(request):
    if request.method == 'POST':
        notification_ids = request.POST.getlist('notification_ids[]')  

        if notification_ids:
            deleted_count, _ = request.user.notifications.filter(id__in=notification_ids).delete()
        else:
            deleted_count, _ = request.user.notifications.all().delete()  

        return JsonResponse({'status': 'success', 'deleted_count': deleted_count})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

def custom_404_view(request, exception):
    return render(request, "404.html", status=404)

@method_decorator(require_http_methods(["POST"]), name='dispatch')
class SearchAPIView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            query = data.get('query', '').strip()

            if not query:
                return JsonResponse({'results': []})

            all_results = [
                {
                    'title': 'Fresh Apples',
                    'description': 'Organic red and green apples from local farms',
                    'url': '/products/apples'
                },
                {
                    'title': 'Banana Bundle', 
                    'description': 'Sweet bananas perfect for smoothies and fruit salads',
                    'url': '/products/bananas'
                },
                {
                    'title': 'Orange Juice',
                    'description': 'Fresh squeezed orange juice with natural pulp',
                    'url': '/products/orange-juice'
                },
                {
                    'title': 'Fruit Salad Recipe',
                    'description': 'Learn how to make the perfect mixed fruit salad',
                    'url': '/articles/fruit-salad-recipe'
                },
                {
                    'title': 'Vegetable Garden Guide',
                    'description': 'Complete guide to growing organic vegetables at home',
                    'url': '/articles/vegetable-garden'
                },
                {
                    'title': 'Healthy Smoothie Tips',
                    'description': 'Best practices for making nutritious fruit smoothies',
                    'url': '/articles/smoothie-tips'
                },
                {
                    'title': 'Apple Pie Recipe',
                    'description': 'Traditional homemade apple pie with crispy crust',
                    'url': '/recipes/apple-pie'
                },
                {
                    'title': 'Organic Farming Methods',
                    'description': 'Sustainable farming techniques for better crops',
                    'url': '/articles/organic-farming'
                },
                {
                    'title': 'Juice Bar Menu',
                    'description': 'Fresh pressed juices and healthy drink options',
                    'url': '/menu/juice-bar'
                },
                {
                    'title': 'Nutrition Facts',
                    'description': 'Essential vitamins and minerals in fruits and vegetables',
                    'url': '/health/nutrition-facts'
                }
            ]

            filtered_results = []
            query_lower = query.lower()

            for result in all_results:
                if (query_lower in result['title'].lower() or 
                    query_lower in result['description'].lower()):
                    filtered_results.append(result)

            return JsonResponse({
                'results': filtered_results[:5],  
                'total': len(filtered_results),
                'query': query
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
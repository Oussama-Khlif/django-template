import os
from django.conf import settings
import json

def notifications_processor(request):
    if request.user.is_authenticated:
        notifications_queryset = request.user.notifications.all()
        unread_count = notifications_queryset.count()  
        latest_notifications = notifications_queryset.order_by('-created_at')[:5]

        return {
            'notifications': latest_notifications,
            'unread_notifications_count': unread_count
        }

    return {
        'notifications': [],
        'unread_notifications_count': 0
    }

def global_settings(request):
    return {
        'SITE_NAME': os.getenv('SITE_NAME', 'DefaultSiteName'),
    }

def user_settings(request):
    user_settings = {}

    if request.user.is_authenticated:
        user_settings = request.user.settings or {}

    return {
        'user_settings': user_settings,
        'user_settings_json': json.dumps(user_settings),
    }
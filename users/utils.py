from django.core.mail import EmailMessage
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

def send_email(to_email, subject, message):
    try:
        email = EmailMessage(
            subject,               
            message,               
            settings.EMAIL_HOST_USER,  
            [to_email],            
        )
        email.content_subtype = "html"  
        email.send(fail_silently=False)
        return True
    except Exception as e:
        return False
    
def check_and_update_login_attempts(request, username, login_successful=False):
    cache_key = f'login_attempts_{username.lower()}'
    attempts_data = cache.get(cache_key) or {'count': 0, 'suspended_until': None}

    if attempts_data.get('suspended_until') and timezone.now() > attempts_data['suspended_until']:
        attempts_data = {'count': 0, 'suspended_until': None}

    if login_successful:
        cache.set(cache_key, {'count': 0, 'suspended_until': None}, timeout=3600)
        return {'allowed': True}

    attempts_data['count'] += 1

    if attempts_data['count'] >= 5:
        attempts_data['suspended_until'] = timezone.now() + timedelta(minutes=30)

    cache.set(cache_key, attempts_data, timeout=3600)

    allowed = attempts_data.get('suspended_until') is None or timezone.now() > attempts_data['suspended_until']
    return {'allowed': allowed}

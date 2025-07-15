from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse
from django.template.loader import render_to_string

class BanCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated and
            getattr(request.user, 'is_banned', False)
        ):
            allowed_paths = [
                reverse('logout'),
                reverse('admin:logout'),
            ]

            if request.path not in allowed_paths:
                html_content = render_to_string('ban.html', request=request)
                return HttpResponse(html_content, status=403)

        return self.get_response(request)

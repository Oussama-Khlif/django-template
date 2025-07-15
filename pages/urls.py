from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('',views.index, name='index'),
    path('settings/',views.settings, name='settings'),
    path('about/',views.about, name='about'),
    path('notifications/get/', views.get_notifications, name='get_notifications'),
    path('notifications/redirect/<int:notification_id>/', views.redirect_and_delete_notification, name='redirect_and_delete_notification'),
    path('notifications/mark-read/', views.delete_notifications, name='delete_notifications'),
    path('api/search/', views.SearchAPIView.as_view(), name='search_api'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.contrib import admin
from django.urls import path, re_path
from django.conf.urls import include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_swagger.views import get_swagger_view

from accounts.view import index
from restapp.urls import urlpatterns as rest_urlpatterns
from django.http import HttpResponse
from django.shortcuts import redirect
from main.views import custom_404


def empty_root(request):
    return HttpResponse("", content_type="text/html; charset=utf-8")
    # return redirect("https://www.google.com")

api_title = 'Smart Savdo API documentation'
schema_view = get_swagger_view(title=api_title, patterns=rest_urlpatterns, url='/api/v1/')

urlpatterns = [
    path('', empty_root),
    re_path(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/v1/admin/', admin.site.urls),
    path('api/v1/', schema_view),
    path('api/v1/docs/', schema_view),
    path('api/v1/', include('restapp.urls')),

    path('api/v1/deadlines', index),
    # path('webhook/api/v1/', include('inspektor.urls_client')), # lekin swagger ko‘rmaydi
]

handler404 = custom_404

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

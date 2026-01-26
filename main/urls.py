from django.contrib import admin
from django.urls import path, re_path
from django.conf.urls import include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_swagger.views import get_swagger_view
from restapp.urls import urlpatterns as rest_urlpatterns
# from inspektor.view import index

api_title = 'Smart Savdo API documentation'
schema_view = get_swagger_view(title=api_title, patterns=rest_urlpatterns, url='/api/v1/')

urlpatterns = [
    re_path(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('admin/', admin.site.urls),
    path('', schema_view),
    path('api/v1/docs/', schema_view),
    path('api/v1/', include('restapp.urls')),

    # path('webhook/api/v1/', include('inspektor.urls_client')), # lekin swagger ko‘rmaydi
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

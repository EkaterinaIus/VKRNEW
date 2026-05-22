from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from learning import views as learning_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', learning_views.index, name='index'),
    path('accounts/', include('accounts.urls')),
    path('learning/', include('learning.urls')),
    path('progress/', include('progress.urls')),
    path('reports/', include('reports.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.contrib import admin
from django.urls import path,include
from triplex import urls as server_api
from results_mng import urls as results_mng_api
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(server_api)),
    path('results/', include(results_mng_api))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

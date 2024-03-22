from django.contrib import admin
from django.urls import path,include
from triplex import urls as server_api
from results_mng import urls as results_mng_api
from promoter_stability_test import urls as results_promoter_stability_test_api
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path(settings.ADMIN_PATH, admin.site.urls),
    path(settings.PUBLIC_API_PATH, include(server_api)),
    path(settings.PRIVATE_API_PATH, include(results_mng_api)),
    path(settings.PRIVATE_API_PATH, include(results_promoter_stability_test_api))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

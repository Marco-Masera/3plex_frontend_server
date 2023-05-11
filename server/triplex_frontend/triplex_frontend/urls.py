from django.contrib import admin
from django.urls import path,include
from triplex import urls as server_api
from results_mng import urls as results_mng_api

urlpatterns = [
    path('api/', include(server_api)),
    path('results/', include(results_mng_api))
]

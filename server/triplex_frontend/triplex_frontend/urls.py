from django.contrib import admin
from django.urls import path,include
from triplex import urls as server_api

urlpatterns = [
    path('api/', include(server_api)),
]

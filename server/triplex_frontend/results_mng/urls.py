from django.urls import path, include
from .views import *


urlpatterns = [
    path('submitresult/<str:token>/', SubmitResult.as_view()),
]

from django.urls import path, include
from .views import *


urlpatterns = [
    path('submitjob/', SubmitjobController.as_view()),
    path('checkjob/<str:token>', CheckjobController.as_view())
]

from django.urls import path, include
from .views import *


urlpatterns = [
    path('submitjob/', SubmitjobController.as_view()),
    path('3plex_default_params', TriplexDefaultParams.as_view()),
    path('checkjob/<str:token>', CheckjobController.as_view()),
    path('checkjobs/email/<str:email>', CheckjobsByEmailController.as_view())
]

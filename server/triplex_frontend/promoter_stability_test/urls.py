from django.urls import path, include
from .views import *


urlpatterns = [
    path('submitresult_promoter/<str:token>/', SubmitResult.as_view()),
    path('submiterror_promoter/<str:token>/', SubmitError.as_view())
]

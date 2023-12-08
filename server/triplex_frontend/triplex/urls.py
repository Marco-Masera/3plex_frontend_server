from django.urls import path, include
from .views import *


urlpatterns = [
    path('submitjob/', SubmitjobController.as_view()),
    path('submit_promoter_test/', SubmitjobPromoterStabilityTestController.as_view()),
    path('jobs/<str:token>/mail/<str:mail>', JobMailController.as_view()),
    path('3plex_default_params', TriplexDefaultParams.as_view()),
    path('checkjob/<str:token>', CheckjobController.as_view()),
    path('checkjobs/email/<str:email>', CheckjobsByEmailController.as_view()),
    path('system_allowed_species_and_iterations', GetAllowedSpecies.as_view()),
    path('search/transcripts/<str:species>/<str:query>', TranscriptsNamesSearchApi.as_view()),
    path('dnatargetsites', GetDnaTargetSitesApi.as_view()),
    path('data_for_visuals/<str:token>', VisualsController.as_view()),
    path('tts_sites/<str:token>/<str:start>/<str:end>/<str:stability>', TTS_Sites_Controller.as_view()),
    path('dbd/<str:token>', DBD_Controller.as_view()),
    path('jobs/<str:token>/websummary', WebSummaryController.as_view()),
    path('jobs/<str:token>/<str:dsDNAID>/profile', ProfileController.as_view()),
    path('jobs/<str:token>/<str:dsDNAID>/<str:stability>/profile_ucsc', ProfileUCSCController.as_view()),
    path('jobs/<str:token>/tpx.xlsx', TPX_to_excel.as_view()),
]

from django.shortcuts import render
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import permissions
from django.core.serializers import serialize
from django.forms.models import model_to_dict
from triplex_frontend.responses import Responses
import json
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import parsers
from triplex_frontend.triplex_exceptions import *
from results_mng.services import ResultsMngServices
from token_queue_mng.services import TokenQueueService
from triplex_frontend.triplex_exceptions import DidNotReceiveInputFilesException, TriplexException, Unauthorized
from .services import PromoterStabilityTestServices

HASHED_TOKEN = "HTOKEN"
class SubmitResult(APIView):
    parser_classes = [parsers.MultiPartParser] 
    def post(self, request, *args, **kwargs):
        token = kwargs.get("token")
        try:
            job = None
            #Check authentication using hmac
            if (not HASHED_TOKEN in request.data):
                raise Unauthorized()
            else:
                hashed_token = request.data[HASHED_TOKEN]
            if (not ResultsMngServices.check_token_hmac(token, hashed_token)):
                raise Unauthorized()

            token_object = TokenQueueService.find_token(kwargs.get("token"))
            token_object.assert_type_promoter_test()
            token_object.assert_state_submitted()
            job = token_object.job

            stability = request.data["STABILITY"]
            summary = request.data["SUMMARY"]
            STABILITY_BEST = request.data["STABILITY_BEST"]
            STABILITY_NORM = request.data["STABILITY_NORM"]
            STABILITY_BEST_FGSEA_RES = request.data["STABILITY_BEST_FGSEA_RES"]
            STABILITY_BEST_LEADING_EDGE = request.data["STABILITY_BEST_LEADING_EDGE"]
            STABILITY_BEST_ENRICHMENT_PLOT = request.data["STABILITY_BEST_ENRICHMENT_PLOT"]
            STABILITY_BEST_STABILITY_COMP_BOXPLOT = request.data["STABILITY_BEST_STABILITY_COMP_BOXPLOT"]
            STABILITY_BEST_STABILITY_COMP = request.data["STABILITY_BEST_STABILITY_COMP"]
            STABILITY_NORM_FGSEA_RES = request.data["STABILITY_NORM_FGSEA_RES"]
            STABILITY_NORM_LEADING_EDGE = request.data["STABILITY_NORM_LEADING_EDGE"]
            STABILITY_NORM_ENRICHMENT_PLOT = request.data["STABILITY_NORM_ENRICHMENT_PLOT"]
            STABILITY_NORM_STABILITY_COMP_BOXPLOT = request.data["STABILITY_NORM_STABILITY_COMP_BOXPLOT"]
            STABILITY_NORM_STABILITY_COMP = request.data["STABILITY_NORM_STABILITY_COMP"]


            if (stability is None or summary is None):
                raise DidNotReceiveInputFilesException()
            if (stability.size == 0 or summary.size == 0):
                raise DidNotReceiveInputFilesException()

            PromoterStabilityTestServices.receive_data(job, stability, summary, STABILITY_BEST, STABILITY_NORM, STABILITY_BEST_FGSEA_RES, STABILITY_BEST_LEADING_EDGE,
    STABILITY_BEST_ENRICHMENT_PLOT, STABILITY_BEST_STABILITY_COMP_BOXPLOT, STABILITY_BEST_STABILITY_COMP,
    STABILITY_NORM_FGSEA_RES, STABILITY_NORM_LEADING_EDGE, STABILITY_NORM_ENRICHMENT_PLOT,
    STABILITY_NORM_STABILITY_COMP_BOXPLOT, STABILITY_NORM_STABILITY_COMP)
            PromoterStabilityTestServices.update_data_last_date(job)
            
        except TriplexException as e:
            if (job is not None):
                ResultsMngServices.set_job_failed(job)  
            return e.handle()
        except Exception as e:
            if (job is not None):
                ResultsMngServices.set_job_failed(job)  
            raise e
        return Responses.success({"ok": "ok"})
    
class SubmitError(APIView):
    parser_classes = [parsers.MultiPartParser] 
    def post(self, request, *args, **kwargs):
        stderr = None; stdout = None
        token = kwargs.get("token")
        try:
            #Check authentication using hmac
            if (not HASHED_TOKEN in request.data):
                raise Unauthorized()
            else:
                hashed_token = request.data[HASHED_TOKEN]
            if (not ResultsMngServices.check_token_hmac(token, hashed_token)):
                raise Unauthorized()
            if (STDOUT in request.data and request.data[STDOUT].size > 0):
                stdout = request.data[STDOUT]
            if (STDERR in request.data and request.data[STDERR].size > 0):
                stderr = request.data[STDERR]
            token_object = TokenQueueService.find_token(token)
            token_object.assert_type_promoter_test()
            job = token_object.job
            PromoterStabilityTestServices.set_job_failed(job, stdout, stderr)  
            return Responses.success({"ok": "ok"})
        except TriplexException as e:
            return e.handle()
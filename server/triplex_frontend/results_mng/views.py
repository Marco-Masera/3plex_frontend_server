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

#Input body as key-value form-data with keys:
STABILITY = "STABILITY"
SUMMARY = "SUMMARY"
PROFILE = "PROFILE"
SECONDARY_STRUCTURE = "SECONDARY_STRUCTURE"
PROFILE_RANDOM = "PROFILE_RANDOM"
STDOUT= "STDOUT"
STDERR = "STDERR"
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
            token_object.assert_type_standard()
            token_object.assert_state_submitted()
            job = token_object.job

            stability = request.data[STABILITY]
            summary = request.data[SUMMARY]
            profile = request.data[PROFILE]
            secondary_struct = request.data[SECONDARY_STRUCTURE]
            profile_random = None
            if (PROFILE_RANDOM in request.data):
                profile_random = request.data[PROFILE_RANDOM]

            if (stability is None or summary is None):
                raise DidNotReceiveInputFilesException()
            if (stability.size == 0 or summary.size == 0):
                raise DidNotReceiveInputFilesException()
            if (profile is None or profile.size == 0):
                raise DidNotReceiveInputFilesException()

            ResultsMngServices.receive_data(job, stability, summary, profile, secondary_struct, profile_random)
            TokenQueueService.notify_all_users_email_job_completed(job)
            ResultsMngServices.update_data_last_date(job)
            
        except TriplexException as e:
            if (job is not None):
                ResultsMngServices.set_job_failed(job)  
                TokenQueueService.notify_all_users_email_job_failed(job)
            return e.handle()
        except Exception as e:
            if (job is not None):
                ResultsMngServices.set_job_failed(job)  
                TokenQueueService.notify_all_users_email_job_failed(job)
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
            token_object.assert_type_standard()
            job = token_object.job
            ResultsMngServices.set_job_failed(job, stdout, stderr)
            TokenQueueService.notify_all_users_email_job_failed(job)  
            return Responses.success({"ok": "ok"})
        except TriplexException as e:
            return e.handle()
        
    
        
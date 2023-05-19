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
from triplex_frontend.triplex_exceptions import DidNotReceiveInputFilesException, TriplexException

#Input body as key-value form-data with keys:
STABILITY = "STABILITY"
SUMMARY = "SUMMARY"

class SubmitResult(APIView):
    parser_classes = [parsers.MultiPartParser] 
    def post(self, request, *args, **kwargs):
        token = kwargs.get("token")
        try:
            stability = request.data[STABILITY]
            summary = request.data[SUMMARY]
            if (stability is None or summary is None):
                raise DidNotReceiveInputFilesException()
            if (stability.size == 0 or summary.size == 0):
                raise DidNotReceiveInputFilesException()

            ResultsMngServices.save_data(token, stability, summary)
            TokenQueueService.set_token_ready(token)
            
        except TriplexException as e:
            TokenQueueService.set_token_failed(token)  
            return e.handle()
        except Exception as e:
            TokenQueueService.set_token_failed(token)  
            raise e
        return Responses.success({"ok": "ok"})
    
class SubmitError(APIView):
    def post(self, request, *args, **kwargs):
        token = kwargs.get("token")
        try:
            TokenQueueService.set_token_failed(token)  
            return Responses.success({"ok": "ok"})
        except TriplexException as e:
            return e.handle()
        
    
        
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import permissions
from django.core.serializers import serialize
from django.forms.models import model_to_dict
from triplex_frontend.responses import Responses
from triplex.services import TriplexService
import json
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import parsers
from triplex_frontend.triplex_exceptions import *
from token_queue_mng.services import TokenQueueService
from results_mng.services import ResultsMngServices

#Input body as key-value form-data with keys:
SSRNA_FASTA = "SSRNA_FASTA" #Fasta file as ssRNA input
DSDNA_FASTA = "DSDNA_FASTA" #Fasta file as dsDNA input
SSRNA_ID = "SSRNA_ID" #Id of the transcript
DSDNA_COORD_BED = "DSDNA_COORD_BED" #Bed file with coordinates

class SubmitjobController(APIView):
    parser_classes = [parsers.MultiPartParser] 

    def post(self, request, *args, **kwargs):
        token = None
        try:
            #Check ssRNA:
            if (SSRNA_FASTA in request.data):
                ssRNA_fasta = request.data[SSRNA_FASTA]
            elif (SSRNA_ID in request.data):
                #TODO get sequence from Id
                raise ModuleNotImplementedYetException()
            else:
                raise SsRnaNotProvidedException()
            #Check dsDNA:
            if (DSDNA_FASTA in request.data):
                dsDNA_fasta = request.data[DSDNA_FASTA]
            elif (DSDNA_COORD_BED in request.data):
                #TODO get sequence from bed file
                raise ModuleNotImplementedYetException()
            else:
                raise DsDnaNotProvidedException()

            #Format triplex_params
            triplex_params = TriplexService.parse_3plex_params(request.data)
            #Get new token
            token = TokenQueueService.get_new_token().token
            #Submit job to backend server
            TriplexService.submit_job(ssRNA_fasta, dsDNA_fasta, token, triplex_params)
            #Initialize data section to receive results
            ResultsMngServices.initialize_data_section(token, ssRNA_fasta, ssDNA_fasta, triplex_params, request.data[SSRNA_ID] if SSRNA_ID in request.data else None )
            return Responses.success({"token": token})
        except TriplexException as e:
            if (token is not None):
                TokenQueueService.remove_token(token)
                try:
                    ResultsMngServices.delete_data_by_token(token)
                except Exception:
                    pass
            return e.handle()

class CheckjobController(APIView):
    def get(self, request, *args, **kwargs):
        try:
            token = kwargs.get("token")
            data = ResultsMngServices.get_data_by_token(token)
            ResultsMngServices.update_data_last_date(token)
            return Responses.success(data)
        except TriplexException as e:
            return e.handle()
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
#Input for extra params
NAME_FIELD = "JOBNAME"
EMAIL_FIELD = "EMAIL"

class SubmitjobController(APIView):
    parser_classes = [parsers.MultiPartParser] 

    def post(self, request, *args, **kwargs):
        tokenObject = None; jobData = None
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
            #Check extra field
            if (EMAIL_FIELD in request.data):
                email = request.data[EMAIL_FIELD]
            else: 
                email = None
            if (NAME_FIELD in request.data): 
                jobName = NAME_FIELD; 
            else:
                jobName = None

            #Format triplex_params
            triplex_params = TriplexService.parse_3plex_params(request.data)
            #Initialize data section to receive results
            jobData = ResultsMngServices.initialize_or_retrieve_data_section(ssRNA_fasta, dsDNA_fasta, triplex_params, request.data[SSRNA_ID] if SSRNA_ID in request.data else None )
            #Get new token
            tokenObject = TokenQueueService.get_new_token(name=jobName, email=email, jobData=jobData)
            #Submit job to backend server
            if (tokenObject.state == "Created"):
                ResultsMngServices.set_job_submitted(jobData)
                TriplexService.submit_job(ssRNA_fasta, dsDNA_fasta, tokenObject.token, triplex_params)
            return Responses.success({"token": tokenObject})
        except TriplexException as e:
            if (tokenObject is not None):
                tokenObject.delete()
            if (jobData is not None):
                try:
                    ResultsMngServices.delete_data_if_orphan(jobData)
                except Exception:
                    pass
            return e.handle()

class CheckjobController(APIView):
    def get(self, request, *args, **kwargs):
        try:
            token = kwargs.get("token")
            #Check that token is ready, else raise exception
            token_object = TokenQueueService.find_token(token)
            if (token_object.check_state_ready()):
                data = ResultsMngServices.get_data_by_token(token)
                ResultsMngServices.update_data_last_date(token)
            else:
                data = {}
            return Responses.success({"job": token_object, "results": data})
        except TriplexException as e:
            return e.handle()

class CheckjobsByEmailController(APIView):
    def get(self, request, *args, **kwargs):
        try:
            email = kwargs.get("email")
            tokens = TokenQueueService.get_tokens_by_email(email)
            return Responses.success(tokens)
        except TriplexException as e:
            return e.handle()
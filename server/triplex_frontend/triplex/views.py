from rest_framework.views import APIView
from rest_framework import status
from rest_framework import permissions
from django.core.serializers import serialize
from django.forms.models import model_to_dict
from triplex_frontend.responses import Responses
from io import StringIO
from django.conf import settings
from triplex.services import TriplexService
import json
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from rest_framework import parsers
from triplex_frontend.triplex_exceptions import *
from token_queue_mng.services import TokenQueueService
from results_mng.services import ResultsMngServices

#Input body as key-value form-data with keys:
SSRNA_FASTA = "SSRNA_FASTA" #Fasta file as ssRNA input
SSRNA_STRING = "SSRNA_STRING" #Sequence like the one in SSRNA_FASTA but provided in string form
DSDNA_FASTA = "DSDNA_FASTA" #Fasta file as dsDNA input
SSRNA_ID = "SSRNA_ID" #Id of the transcript
DSDNA_COORD_BED = "DSDNA_COORD_BED" #Bed file with coordinates
DSDNA_TARGET_NAME = "DSDNA_TARGET_NAME"
#Input for extra params
NAME_FIELD = "JOBNAME"
EMAIL_FIELD = "EMAIL"

class SubmitjobController(APIView):
    parser_classes = [parsers.MultiPartParser] 

    def post(self, request, *args, **kwargs):
        tokenObject = None; jobData = None; ssRNA_id = None
        try:
            #Check ssRNA:
            ssRNA_fasta = None
            if (SSRNA_FASTA in request.data):
                ssRNA_fasta = request.data[SSRNA_FASTA]
            elif (SSRNA_STRING in request.data):
                #Verify size of string before creating the fake InMemoryFile
                if (len(request.data[SSRNA_STRING]) > settings.SSRNA_MAX_SIZE):
                    raise InputFileTooBig(f"Your ssRNA string file exceed our limit of {settings.SSRNA_MAX_SIZE} characters")
                buff = StringIO(request.data[SSRNA_STRING])
                buff.seek(0)
                ssRNA_fasta = InMemoryUploadedFile(buff,'file',"ssRNA",None,buff.tell(),None)
            elif (SSRNA_ID in request.data):
                ssRNA_id = request.data["SSRNA_ID"]
            else:
                raise SsRnaNotProvidedException()
            #Check dsDNA:
            if (DSDNA_FASTA in request.data):
                dsDNA_fasta = request.data[DSDNA_FASTA]
            elif (DSDNA_COORD_BED in request.data):
                #TODO get sequence from bed file
                raise ModuleNotImplementedYetException()
            elif (DSDNA_TARGET_NAME in request.data):
                #todo use target site in db
                raise ModuleNotImplementedYetException()
            else:
                raise DsDnaNotProvidedException()
            #Check extra field
            if (EMAIL_FIELD in request.data):
                email = request.data[EMAIL_FIELD]
            else: 
                email = None
            if (NAME_FIELD in request.data): 
                jobName = request.data[NAME_FIELD]; 
            else:
                jobName = None

            if (ssRNA_fasta is not None):
                if (not isinstance(ssRNA_fasta,InMemoryUploadedFile) and not isinstance(ssRNA_fasta, TemporaryUploadedFile)):
                    raise SsRnaNotProvidedException() 
                if (ssRNA_fasta.size > settings.SSRNA_MAX_SIZE):
                    raise InputFileTooBig(f"Your ssRNA fasta file exceed our limit of {settings.SSRNA_MAX_SIZE} bytes")
                #rename input files
                ssRNA_fasta.name = settings.SSRNA_BASE_NAME 
                #Adjust header of ssRNA
                ssRNA_fasta = TriplexService.adjust_ssRNA_header(ssRNA_fasta)
            
            if (dsDNA_fasta is not None):
                if (not isinstance(dsDNA_fasta,InMemoryUploadedFile) and not isinstance(dsDNA_fasta, TemporaryUploadedFile)):
                    raise DsDnaNotProvidedException()
                if (dsDNA_fasta.size > settings.DSDNA_MAX_SIZE):
                    raise InputFileTooBig(f"Your dsDNA fasta file exceed our limit of {settings.DSDNA_MAX_SIZE} bytes")
                dsDNA_fasta.name = settings.DSDNA_BASE_NAME

        
            #Format triplex_params
            triplex_params = TriplexService.parse_3plex_params(request.data)
            #Validate them 
            TriplexService.validate_triplex_params(triplex_params)
            #Initialize data section to receive results
            jobData = ResultsMngServices.initialize_or_retrieve_data_section(ssRNA_fasta, dsDNA_fasta, triplex_params, ssRNA_id)
            if (ssRNA_fasta is None):
                ssRNA_fasta = open(jobData.ssRNA_id.ssRNA_fasta_path, 'rb')
            #Get new token
            tokenObject = TokenQueueService.get_new_token(name=jobName, email=email, jobData=jobData)
            #Submit job to backend server
            if (tokenObject.state == "Created"):
                #Todo se Id invece di ssRNA
                ResultsMngServices.set_job_submitted(jobData)
                TriplexService.submit_job(ssRNA_fasta, dsDNA_fasta, tokenObject.token, triplex_params)
            else:
                TokenQueueService.notify_user_email_job_completed(tokenObject)
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
        except Exception as e:
            if (tokenObject is not None):
                tokenObject.delete()
            if (jobData is not None):
                try:
                    ResultsMngServices.delete_data_if_orphan(jobData)
                except Exception:
                    pass
            raise e
        #finally:
        #    ssRNA_fasta.close()


class CheckjobController(APIView):
    def get(self, request, *args, **kwargs):
        try:
            token = kwargs.get("token")
            #Check that token is ready, else raise exception
            token_object = TokenQueueService.find_token(token)
            if (token_object.check_state_ready() or token_object.check_state_failed()):
                data = ResultsMngServices.get_data_by_token(token)
                params = ResultsMngServices.get_triplex_params(token)
                ResultsMngServices.update_data_last_date(token)
            else:
                data = {}
                params = ResultsMngServices.get_triplex_params(token)
            return Responses.success({"job": token_object, "results": data, "params": params})
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

class TriplexDefaultParams(APIView):
    def get(self, request, *args, **kwargs):
        try:
            params = TriplexService.get_triplex_default_params_bounds_and_description()
            return Responses.success(params)
        except TriplexException as e:
            return e.handle()

class TranscriptsNamesSearchApi(APIView):
    def get(self, request, *args, **kwargs):
        query = kwargs.get("query")
        species = kwargs.get("species")
        max_elems = request.query_params.get('max_elems')
        transcripts = ResultsMngServices.search_longest_transcripts(query, species, max_elems)
        return Responses.success(list(transcripts))

class GetDnaTargetSitesApi(APIView):
    def get(self, request, *args, **kwargs):
        transcripts = ResultsMngServices.get_dna_target_sites()
        return Responses.success(list(transcripts))

class VisualsController(APIView):
    def get(self, request, *args, **kwargs):
        try:
            token = kwargs.get("token")
            token_object = TokenQueueService.find_token(token)
            #If token not ready return error
            token_object.assert_state_ready()
            #Retrieve data for visualizations
            data = ResultsMngServices.get_data_for_visuals(token)
            ResultsMngServices.update_data_last_date(token)
            
            return Responses.success({"job": token_object, "available": data})
        except TriplexException as e:
            return e.handle()

class GetAllowedSpecies(APIView):
    def get(self, request, *args, **kwargs):
        try:
            return Responses.success([species[0] for species in settings.ALLOWED_SPECIES])
        except TriplexException as e:
            return e.handle()
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
from rest_framework.authentication import SessionAuthentication, BasicAuthentication 

class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening

class SubmitjobController(APIView):
    parser_classes = [parsers.MultiPartParser] 
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    def post(self, request, *args, **kwargs):
        tokenObject = None; jobData = None;
        try:
            #Parse request parameters
            ssRNA_fasta, dsDNA_fasta, dsDNA_bed, dsDNA_precomputed, species, ssRNA_id, email, jobName, use_randomization = TriplexService.parse_request_params(request)
            #Validate and rename ssRNA_fasta
            ssRNA_fasta = TriplexService.validate_and_rename_ssRNA_fasta(ssRNA_fasta)
            #Validate and rename dsDNA file(s)
            dsDNA_file = TriplexService.validate_and_rename_dsDNA(dsDNA_fasta, dsDNA_bed, species)
            #Format triplex_params
            triplex_params = TriplexService.parse_3plex_params(request.data)
            #Validate them 
            TriplexService.validate_triplex_params(triplex_params)

            #Initialize data section to receive results
            jobData = ResultsMngServices.initialize_or_retrieve_data_section(ssRNA_fasta, dsDNA_file, dsDNA_precomputed, 
                triplex_params, ssRNA_id, species, use_randomization=use_randomization)
            #If the ssRNA is specified by ID, open the corresponding file
            if (ssRNA_fasta is None):
                ssRNA_fasta = open(jobData.ssRNA_id.ssRNA_fasta_path, 'rb')
            if (dsDNA_precomputed):
                dsDNA_precomputed = jobData.dsDNA_precomputed_target.filename
            #Get new token
            tokenObject = TokenQueueService.get_new_token(name=jobName, email=email, jobData=jobData)
            #Submit job to backend server
            if (tokenObject.state == "Created"):
                #Todo se Id invece di ssRNA
                ResultsMngServices.set_job_submitted(jobData)
                TriplexService.submit_job(ssRNA_fasta, dsDNA_file, dsDNA_precomputed, tokenObject.token, triplex_params, species, use_randomization)
            elif (tokenObject.state == "Ready"):
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
            return Responses.success({
                "species": [species[0] for species in settings.ALLOWED_SPECIES],
                "iterations":  settings.ALLOWED_RANDOMIZATION_ITERATIONS
                })
        except TriplexException as e:
            return e.handle()
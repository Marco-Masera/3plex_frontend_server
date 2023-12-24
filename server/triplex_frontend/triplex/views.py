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
from visualization.visualization_utils import VisualizationUtils
from promoter_stability_test.services import PromoterStabilityTestServices

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
            ssRNA_fasta, dsDNA_fasta, dsDNA_bed, dsDNA_precomputed, species, ssRNA_id, email, jobName, use_randomization = TriplexService.parse_request_params_normal_job(request)
            #Validate and rename ssRNA_fasta
            ssRNA_fasta = TriplexService.validate_and_rename_ssRNA_fasta(ssRNA_fasta)
            #Validate and rename dsDNA file(s)
            dsDNA_file = TriplexService.validate_and_rename_dsDNA(dsDNA_fasta, dsDNA_bed, species)
            is_bed_dsDNA = dsDNA_bed is not None
            #Format triplex_params
            triplex_params = TriplexService.parse_3plex_params(request.data)
            #Validate them 
            TriplexService.validate_triplex_params(triplex_params)

            #Initialize data section to receive results
            jobData = ResultsMngServices.initialize_or_retrieve_data_section(ssRNA_fasta, dsDNA_file, dsDNA_precomputed, 
                triplex_params, ssRNA_id, species, use_randomization=use_randomization, is_bed = is_bed_dsDNA)
            #If the ssRNA is specified by ID, open the corresponding file
            if (ssRNA_fasta is None):
                ssRNA_fasta = open(jobData.ssRNA_id.ssRNA_fasta_path, 'rb')
            if (dsDNA_precomputed):
                dsDNA_precomputed = jobData.dsDNA_precomputed_target.filename
            #Get new token
            tokenObject = TokenQueueService.get_new_token(name=jobName, email=email, jobData=jobData)
            #Submit job to backend server
            if (tokenObject.state == "Created"):
                ResultsMngServices.set_job_submitted(jobData)
                TriplexService.submit_job(ssRNA_fasta, dsDNA_file, dsDNA_precomputed, tokenObject.token, triplex_params, species, use_randomization, is_bed=is_bed_dsDNA)
            elif (tokenObject.state == "Ready"):
                TokenQueueService.notify_user_email_job_completed(tokenObject)
            return Responses.success({"token": tokenObject})
        except TriplexException as e:
            if (tokenObject is not None):
                tokenObject.delete()
            if (jobData is not None):
                try:
                    TokenQueueService.delete_data_if_orphan(jobData)
                except Exception:
                    pass
            return e.handle()
        except Exception as e:
            if (tokenObject is not None):
                tokenObject.delete()
            if (jobData is not None):
                try:
                    TokenQueueService.delete_data_if_orphan(jobData)
                except Exception:
                    pass
            raise e

class SubmitjobPromoterStabilityTestController(APIView):
    parser_classes = [parsers.MultiPartParser] 
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    def post(self, request, *args, **kwargs):
        tokenObject = None; jobData = None;
        try:
            #Parse request parameters
            ssRNA_fasta, all_genes, interest_genes, species, ssRNA_id, email, jobName = TriplexService.parse_request_params_promoter_stability_test(request)
            #Validate and rename ssRNA_fasta
            ssRNA_fasta = TriplexService.validate_and_rename_ssRNA_fasta(ssRNA_fasta)
            #Validate genes
            TriplexService.validate_genes_for_promoter_stability_test(all_genes, interest_genes)
            #Format triplex_params
            triplex_params = TriplexService.parse_3plex_params(request.data)
            #Validate them 
            TriplexService.validate_triplex_params(triplex_params)
            
            #If the ssRNA is specified by ID, open the corresponding file
            if (ssRNA_fasta is None):
                ssRNA_fasta = open(jobData.ssRNA_id.ssRNA_fasta_path, 'rb')
            
            data_object = PromoterStabilityTestServices.initialize_data_section(ssRNA_fasta, ssRNA_id,  all_genes, interest_genes, species, triplex_params)
            #1- Generate token and data structure to host data - memorize ssRNA and gene lists
            token_object = TokenQueueService.get_new_token(name=jobName, email=email, jobData=data_object)
            #  1.1- Add this new class to stuff to be cleaned up by the cleanup service
            #2- Send request to backend server
            TriplexService.submit_promoter_stability_test_job(token_object.token, interest_genes, all_genes, ssRNA_fasta, triplex_params, species)
            PromoterStabilityTestServices.set_job_submitted(data_object)
            return Responses.success({"token": token_object})
        except TriplexException as e:
            if (token_object is not None):
                token_object.delete()
            if (data_object is not None):
                data_object.delete()
            return e.handle()

class JobMailController(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    def post(self, request, *args, **kwargs):
        try:
            token = kwargs.get("token")
            mail = kwargs.get("mail")
            TokenQueueService.update_token_email(token, mail)
            return Responses.success(None)
        except TriplexException as e:
            return e.handle()

class CheckjobController(APIView):
    def get(self, request, *args, **kwargs):
        try:
            token = kwargs.get("token")
            #Check that token is ready, else raise exception
            token_object = TokenQueueService.find_token(token)
            data, params = TokenQueueService.getDataFromToken(token_object)
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
            dsDNA_id = request.query_params.get('dsDNAID')
            token_object = TokenQueueService.find_token(token)
            #If token not ready return error
            token_object.assert_state_ready()
            #If not token is standard job, return error
            token_object.assert_type_standard()
            #Retrieve data for visualizations
            data = VisualizationUtils.get_data_for_visuals(token_object.job, token, dsDNA_id)
            ResultsMngServices.update_data_last_date(token)
            
            return Responses.success({"job": token_object, "available": data})
        except TriplexException as e:
            return e.handle()

class TTS_Sites_Controller(APIView):
    def get(self, request, *args, **kwargs):
        try:
            token = kwargs.get("token")
            start = int(kwargs.get("start"))
            end = int(kwargs.get("end"))
            stability = float(kwargs.get("stability"))
            dsDNAID = request.query_params.get('dsdnaid')
            #Retrieve job data
            token_object = TokenQueueService.find_token(token)
            token_object.assert_type_standard()
            data = token_object.job
            values = VisualizationUtils.find_tpx_in_interval(data, start, end, stability, dsDNAID)
            ResultsMngServices.update_data_last_date(token)
            return Responses.success({"data": values})
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

class DBD_Controller(APIView):
    parser_classes = (parsers.MultiPartParser,)
    def get(self, request, *args, **kwargs):
        try:
            token = TokenQueueService.find_token(kwargs.get("token"))
            dbds = TokenQueueService.get_dbds(token)
            return Responses.success(dbds)
        except TriplexException as e:
            return e.handle()
    
    def post(self, request, *args, **kwargs):
        try:
            token = TokenQueueService.find_token(kwargs.get("token"))
            TokenQueueService.set_dbds(token, json.loads(request.data["dbds"]))
            return Responses.success(None)
        except TriplexException as e:
            return e.handle()

class WebSummaryController(APIView):
    def get(self, request, *args, **kwargs):
        try:
            token_object = TokenQueueService.find_token(kwargs.get("token"))
            token_object.assert_type_standard()
            job = token_object.job
            return Responses.success(VisualizationUtils.get_web_summary(job))
        except TriplexException as e:
            return e.handle()

class ProfileController(APIView):
    def get(self, request, *args, **kwargs):
        try:
            token_object = TokenQueueService.find_token(kwargs.get("token"))
            token_object.assert_type_standard()
            job = token_object.job
            dsDNAID = kwargs.get("dsDNAID")
            result = VisualizationUtils.get_profile_dsDNAID(job, dsDNAID)
            return Responses.binary(result)
        except TriplexException as e:
            return e.handle()

class ProfileUCSCController(APIView):
    def get(self, request, *args, **kwargs):
        try:
            token_object = TokenQueueService.find_token(kwargs.get("token"))
            token_object.assert_type_standard()
            job = token_object.job
            dsDNAID = kwargs.get("dsDNAID")
            stability = float(kwargs.get("stability"))
            result = VisualizationUtils.get_trace_for_genome_browser(job, dsDNAID, stability)
            return Responses.success(result)
        except TriplexException as e:
            return e.handle()

class TPX_to_excel(APIView):
    def get(self, request, *args, **kwargs):
        try:
            token_object = TokenQueueService.find_token(kwargs.get("token"))
            token_object.assert_type_standard()
            job = token_object.job
            dsDNAID = request.query_params.get("dsDNAID")
            stability = request.query_params.get("stability")
            start = request.query_params.get("start")
            end = request.query_params.get("end")
            if (stability is None or start is None or end is None) and (dsDNAID is None):
                raise TPXNotFound()

            if not (stability is None or start is None or end is None):
                tpx = VisualizationUtils.find_tpx_in_interval(job, start, end, stability, dsDNA_id=dsDNAID)
            else:
                tpx = VisualizationUtils.get_tpx_by_dsDNAID(job, dsDNAID, stability)
            return Responses.binary(VisualizationUtils.export_tpx_in_excel(tpx))
        except TriplexException as e:
            return e.handle()
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import permissions
from django.core.serializers import serialize
from django.forms.models import model_to_dict
from triplex_frontend import responses
from triplex.services import TriplexService
import json


class SubmitjobController(APIView):
    def post(self, request, *args, **kwargs):
        pass

class CheckjobController(APIView):
    def get(self, request, *args, **kwargs):
        token = kwargs.get("token")
        pass

"""
class TranscriptsNamesApi(APIView):
    def get(self, request, *args, **kwargs):
        transcripts = LncRNAService.get_all_transcripts() 
        return Responses.success(list(transcripts))

class TranscriptsNamesSearchApi(APIView):
    def get(self, request, *args, **kwargs):
        max_elems = request.query_params.get('max_elems')
        transcripts = LncRNAService.search_between_transcripts(kwargs.get(LNC_QUERY), max_elems)
        return Responses.success(list(transcripts))

class FullTranscriptApi(APIView):
    def get(self, request, *args, **kwargs):
        transcripts = LncRNAService.get_full_transcript(kwargs.get(LNC_TRANSCRIPT_ID))
        if (transcripts==False):
            return Responses.notFound(f"Cannot find transcript with id {kwargs.get(LNC_TRANSCRIPT_ID)}")
        return Responses.success(transcripts)

class ConservationApi(APIView):
    def get(self, request, *args, **kwargs):
        transcript_id = kwargs.get(LNC_TRANSCRIPT_ID)
        signal = LncRNAService.get_conservation(transcript_id)
        if (signal==False):
            return Responses.notFound(f"Cannot find conservation for transcript with id {transcript_id}")
        return Responses.success(signal) 

class RepeatsApi(APIView):
    def get(self, request, *args, **kwargs):
        transcript_id = kwargs.get(LNC_TRANSCRIPT_ID)
        repeats = LncRNAService.get_repeats(transcript_id)
        return Responses.success(list(repeats))

class SecondaryStructureApi(APIView):
    def get(self, request, *args, **kwargs):
        lnc_name = kwargs.get(LNC_NAME_ARG)
        species = kwargs.get(LNC_SPECIES_ARG)
        signal = LncRNAService.get_secondary_structure(species, lnc_name)
        if (signal==False):
            return Responses.notFound(f"Cannot find conservation for transcript with id {transcript_id}")
        return Responses.success(signal) 

class TTSApi(APIView):
    def get(self, request, *args, **kwargs):
        lnc_name = kwargs.get(LNC_NAME_ARG)
        species = kwargs.get(LNC_SPECIES_ARG)
        return Responses.success(LncRNAService.get_tts(species, lnc_name))   
"""
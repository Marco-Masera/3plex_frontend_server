from token_queue_mng.models import *
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.conf import settings
import requests
from io import StringIO
import datetime
import hmac
from triplex_frontend.triplex_exceptions import *
from results_mng.models import GeneInDnaTargetSite

#Input body as key-value form-data with keys:
SSRNA_FASTA = "SSRNA_FASTA" #Fasta file as ssRNA input
SSRNA_STRING = "SSRNA_STRING" #Sequence like the one in SSRNA_FASTA but provided in string form
DSDNA_FASTA = "DSDNA_FASTA" #Fasta file as dsDNA input
SSRNA_ID = "SSRNA_ID" #Id of the transcript
DSDNA_COORD_BED = "DSDNA_COORD_BED" #Bed file with coordinates
DSDNA_TARGET_NAME = "DSDNA_TARGET_NAME"
USE_RAND = "USE_RAND"
#Input for extra params
NAME_FIELD = "JOBNAME"
EMAIL_FIELD = "EMAIL"
SPECIES_FIELD = "SPECIES"

default_triplex_params = {
    'min_len': 10,
    'max_len': -1,
    'error_rate': 20,
    'guanine_rate': 40,
    'filter_repeat': "off",
    'consecutive_errors': 1,
    'SSTRAND': 0
}
triplex_params_description = {
    'min_len': "Minimum triplex length required. Minimum: 6",
    'max_len': "Maximum triplex length permitted, M=-1 imply no limit.",
    'error_rate': "Maximal percentage of error allowed in a triplex. Max 20.",
    'guanine_rate': "Minimal guanine percentage required in any TTS.",
    'filter_repeat': "If enabled, exclude repeat and low complexity regions.",
    'consecutive_errors': "Maximum number of consecutive errors allowed in a triplex.",
    'SSTRAND': "Percentage of masked RNA nucleotides based on RNAplfold base pairing probabilities."
}
#Inclusive bounds for the params. None is meant as boundless
triplex_params_bounds = {
    'min_len': [6, None],
    'max_len': [-1, None],
    'error_rate': [0, 20],
    'guanine_rate': [1, 100],
    'filter_repeat': None,
    'consecutive_errors': [0, None],
    'SSTRAND': [0, 100]
}

def get_time_based_otp(token):
    timestamp = f"{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H}"
    h = hmac.new(bytes(settings.HMAC_KEY, 'utf-8'), msg=bytes(token+timestamp, 'utf-8'), digestmod='sha256')
    digested = h.hexdigest()
    return digested

class TriplexService:
    
    def get_triplex_default_params_bounds_and_description():
        r = dict()
        for elem in default_triplex_params.keys():
            r[elem] = {"bounds": triplex_params_bounds[elem], "default": default_triplex_params[elem], "description": triplex_params_description[elem]}
        return r

    def validate_triplex_params(params: dict):
        for param in params.keys():
            bounds = triplex_params_bounds[param]
            if (bounds is None):
                continue
            try:
                value = int(params[param])
            except ValueError:
                raise TriplexParamOutOfBound(f"3plex param {param} has illegal value {params[param]}")
            if (bounds[0] is not None and bounds[0] > value):
                raise TriplexParamOutOfBound(f"3plex param {param} is set to {params[param]} but its lower limit is {bounds[0]}")
            if (bounds[1] is not None and bounds[1] < value):
                raise TriplexParamOutOfBound(f"3plex param {param} is set to {params[param]} but its upper limit is {bounds[1]}")

    def submit_promoter_stability_test_job(token: str, genes_interest, genes_all, ssRNA_fasta, triplex_params, species):
        ssRNA_fasta.seek(0)
        url = settings.BACKEND_URL+f"/submit_promoter_test/{token}"
        query_params = []
        query_params.append(f"hmac={get_time_based_otp(token)}")
        if (species is not None):
            query_params.append(f"species={species}")
        query_params.append(f"debug={settings.DEBUG}")
        if (len(query_params)>0):
            url = f"{url}?{ '&'.join(query_params) }"
        files = {'ssRNA_fasta': ssRNA_fasta}
        triplex_tuples = [(key, triplex_params[key]) for key in triplex_params.keys()]
        triplex_tuples += [("genes_interest", ",".join(genes_interest)), ("genes_all", ",".join(genes_all))]
        try:
            r = requests.post(url, files=files, data=triplex_tuples)
            if (r.status_code != 200):
                print(f"Bad response: {r.content}")
                raise CannotSubmitToBackendException()
        except Exception as e:
            print(e)
            raise CannotSubmitToBackendException()

    def submit_job(ssRNA_fasta, dsDNA_fasta, dsDNA_precomputed, token: str, triplex_params, species, use_randomization=0, is_bed=False):
        ssRNA_fasta.seek(0)
        if (dsDNA_fasta):
            dsDNA_fasta.seek(0)
        url = settings.BACKEND_URL+f"/submit/{token}"
        query_params = []
        query_params.append(f"hmac={get_time_based_otp(token)}")
        if (species is not None):
            query_params.append(f"species={species}")
        if (dsDNA_precomputed is not None):
            query_params.append(f"dsdna_target={dsDNA_precomputed}")
        if (use_randomization):
            query_params.append(f"use_random={use_randomization}")
        query_params.append(f"is_bed={is_bed}")
        query_params.append(f"debug={settings.DEBUG}")
        if (len(query_params)>0):
            url = f"{url}?{ '&'.join(query_params) }"
        files = {'ssRNA_fasta': ssRNA_fasta, 'dsDNA_fasta': dsDNA_fasta}
        triplex_tuples = [(key, triplex_params[key]) for key in triplex_params.keys()]
        try:
            r = requests.post(url, files=files, data=triplex_tuples)
            if (r.status_code != 200):
                print(f"Bad response: {r.content}")
                raise CannotSubmitToBackendException()
        except Exception as e:
            print(e)
            raise CannotSubmitToBackendException()
        

    def parse_3plex_params(data):
        return {
            'min_len': data.get('min_len', default_triplex_params['min_len']),
            'max_len': data.get('max_len', default_triplex_params['max_len']),
            'error_rate': data.get('error_rate', default_triplex_params['error_rate']),
            'guanine_rate': data.get('guanine_rate', default_triplex_params['guanine_rate']),
            'filter_repeat': data.get('filter_repeat', default_triplex_params['filter_repeat']),
            'consecutive_errors': data.get('consecutive_errors', default_triplex_params['consecutive_errors']),
            'SSTRAND': data.get('SSTRAND', default_triplex_params['SSTRAND'])
        }

    def adjust_ssRNA_header(ssRNA:InMemoryUploadedFile):
        first_line = ssRNA.readline()
        new_file = StringIO()
        #InMemoryUploadedFile can come in 2 encodings: text or binary. They need to be managed differently
        if (type(first_line)==str):
            if (not first_line.startswith(">")):
                ssRNA.seek(0)
            new_file.write(f">{settings.SSRNA_HEADER }\n")
            while True:
                data = ssRNA.read(65536)
                if not data:
                    break
                new_file.write(data)
        else:
            first_line = first_line.decode()
            if (not first_line.startswith(">")):
                ssRNA.seek(0)
            new_file.write(f">{settings.SSRNA_HEADER }\n")
            while True:
                data = ssRNA.read(65536).decode()
                if not data:
                    break
                new_file.write(data)
        new_file.seek(0)
        ssRNA_fasta = InMemoryUploadedFile(new_file,'file',"ssRNA.fa",None,new_file.tell(),None)
        return ssRNA_fasta

    def parse_request_params_normal_job(request):
        #Check ssRNA:
        ssRNA_fasta = None; dsDNA_fasta = None; dsDNA_bed = None; dsDNA_precomputed = None
        species = None; ssRNA_id = None; email=None; jobName = None

        if (SSRNA_FASTA in request.data):
            ssRNA_fasta = request.data[SSRNA_FASTA]
        elif (SSRNA_STRING in request.data):
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
            #Uses bed file
            dsDNA_bed = request.data[DSDNA_COORD_BED]
        elif (DSDNA_TARGET_NAME in request.data):
            dsDNA_precomputed = request.data[DSDNA_TARGET_NAME]
        else:
            raise DsDnaNotProvidedException()
        #Check randomization
        if (USE_RAND in request.data):
            use_randomization = request.data[USE_RAND]
            print(use_randomization)
            print(settings.ALLOWED_RANDOMIZATION_ITERATIONS)
            if (not int(use_randomization) in settings.ALLOWED_RANDOMIZATION_ITERATIONS):
                raise NumIterationsNotAllowed()
        else:
            use_randomization = 0
        #Check extra field
        if (EMAIL_FIELD in request.data):
            email = request.data[EMAIL_FIELD]
        else: 
            email = None
        if (NAME_FIELD in request.data): 
            jobName = request.data[NAME_FIELD]; 
        else:
            jobName = None
        if (SPECIES_FIELD in request.data):
            species = request.data[SPECIES_FIELD]
            if (not (species,species) in  settings.ALLOWED_SPECIES):
                raise SpeciesNotSupportedException()
        
        return ssRNA_fasta, dsDNA_fasta, dsDNA_bed, dsDNA_precomputed, species, ssRNA_id, email, jobName, use_randomization

    def parse_request_params_promoter_stability_test(request):
        #Check ssRNA:
        ssRNA_fasta = None
        species = None; ssRNA_id = None; email=None; jobName = None

        if (SSRNA_FASTA in request.data):
            ssRNA_fasta = request.data[SSRNA_FASTA]
        elif (SSRNA_STRING in request.data):
            if (len(request.data[SSRNA_STRING]) > settings.SSRNA_MAX_SIZE):
                raise InputFileTooBig(f"Your ssRNA string file exceed our limit of {settings.SSRNA_MAX_SIZE} characters")
            buff = StringIO(request.data[SSRNA_STRING])
            buff.seek(0)
            ssRNA_fasta = InMemoryUploadedFile(buff,'file',"ssRNA",None,buff.tell(),None)
        elif (SSRNA_ID in request.data):
            ssRNA_id = request.data["SSRNA_ID"]
        else:
            raise SsRnaNotProvidedException()
        if ("putative_genes" in request.data):
            putative_genes = request.data["putative_genes"].split(",")
        else:
            raise DsDnaNotProvidedException()
        if ("background_genes" in request.data):
            background_genes = request.data["background_genes"].split(",")
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
        if (SPECIES_FIELD in request.data):
            species = request.data[SPECIES_FIELD]
            if (not (species,species) in  settings.ALLOWED_SPECIES):
                raise SpeciesNotSupportedException()
        
        return ssRNA_fasta, putative_genes, background_genes, species, ssRNA_id, email, jobName


    def validate_genes_for_promoter_stability_test(putative_genes, background_genes):
        pass 
        #Check that background genes are included in putative
        if not (set(background_genes).issubset(set(putative_genes))):
            raise BackgroundGenesNotIncludedInPutative()
        #Check that all genes are included in MANE
        not_included = []
        for elem in putative_genes:
            if (GeneInDnaTargetSite.objects.filter(name=elem).count()==0):
                not_included.append(elem)
        if (len(not_included)>0):
            raise BackgroundGenesNotIncludedInMANE(not_included) 

    def validate_and_rename_ssRNA_fasta(ssRNA_fasta):
        if (ssRNA_fasta is not None):
            if (not isinstance(ssRNA_fasta,InMemoryUploadedFile) and not isinstance(ssRNA_fasta, TemporaryUploadedFile)):
                raise SsRnaNotProvidedException() 
            if (ssRNA_fasta.size > settings.SSRNA_MAX_SIZE):
                raise InputFileTooBig(f"Your ssRNA fasta file exceed our limit of {settings.SSRNA_MAX_SIZE} bytes")
            #rename input files
            ssRNA_fasta.name = settings.SSRNA_BASE_NAME 
            #Adjust header of ssRNA
            ssRNA_fasta = TriplexService.adjust_ssRNA_header(ssRNA_fasta)
        return ssRNA_fasta
    
    def validate_and_rename_dsDNA(dsDNA_fasta, dsDNA_bed, species):
        file_to_return = None
        if (dsDNA_fasta is not None):
            if (not isinstance(dsDNA_fasta,InMemoryUploadedFile) and not isinstance(dsDNA_fasta, TemporaryUploadedFile)):
                raise DsDnaNotProvidedException()
            if (dsDNA_fasta.size > settings.DSDNA_MAX_SIZE):
                raise InputFileTooBig(f"Your dsDNA fasta file exceed our limit of {settings.DSDNA_MAX_SIZE} bytes")
            dsDNA_fasta.name = settings.DSDNA_BASE_NAME
            file_to_return = dsDNA_fasta
        if (dsDNA_bed is not None):
            if (not isinstance(dsDNA_bed,InMemoryUploadedFile) and not isinstance(dsDNA_bed, TemporaryUploadedFile)):
                raise DsDnaNotProvidedException()
            if (dsDNA_bed.size > settings.DSDNA_MAX_SIZE):
                raise InputFileTooBig(f"Your dsDNA bed file exceed our limit of {settings.DSDNA_MAX_SIZE} bytes")
            dsDNA_bed.name = settings.DSDNA_BED_BASE_NAME
            if (species is None):
                raise SpeciesNotProvidedException()
            file_to_return = dsDNA_bed
        return file_to_return 
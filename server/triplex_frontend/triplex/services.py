from token_queue_mng.models import *
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.conf import settings
import requests
from io import StringIO
from triplex_frontend.triplex_exceptions import CannotSubmitToBackendException, TriplexParamOutOfBound

default_triplex_params = {
    'min_len': 8,
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

    def submit_job(ssRNA_fasta, dsDNA_fasta, token: str, triplex_params):
        ssRNA_fasta.seek(0)
        dsDNA_fasta.seek(0)
        print(ssRNA_fasta)
        url = settings.BACKEND_URL+f"/submit/{token}"
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
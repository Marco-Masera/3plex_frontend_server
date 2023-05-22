from token_queue_mng.models import *
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings
import requests
from io import StringIO
from triplex_frontend.triplex_exceptions import CannotSubmitToBackendException

default_triplex_params = {
    'min_len': 8,
    'max_len': -1,
    'error_rate': 20,
    'guanine_rate': 40,
    'filter_repeat': "off",
    'consecutive_errors': 1,
    'SSTRAND': 0
}

class TriplexService:
    
    def submit_job(ssRNA_fasta: InMemoryUploadedFile, dsDNA_fasta: InMemoryUploadedFile, token: str, triplex_params):
        ssRNA_fasta.seek(0)
        dsDNA_fasta.seek(0)
        url = settings.BACKEND_URL+f"/submit/{token}"
        files = {'ssRNA_fasta': ssRNA_fasta, 'dsDNA_fasta': dsDNA_fasta}
        triplex_tuples = [(key, triplex_params[key]) for key in triplex_params.keys()]
        try:
            r = requests.post(url, files=files, data=triplex_tuples)
            if (r.status_code != 200):
                raise CannotSubmitToBackendException()
        except:
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
        if (type(first_line)==str):
            if (not first_line.startswith(">")):
                ssRNA.seek(0)
            new_file.write(">ssRNA\n")
            while True:
                data = ssRNA.read(65536)
                if not data:
                    break
                new_file.write(data)
        else:
            first_line = first_line.decode()
            if (not first_line.startswith(">")):
                ssRNA.seek(0)
            new_file.write(">ssRNA\n")
            while True:
                data = ssRNA.read(65536).decode()
                if not data:
                    break
                new_file.write(data)
        new_file.seek(0)
        ssRNA_fasta = InMemoryUploadedFile(new_file,'file',"ssRNA.fa",None,new_file.tell(),None)
        return ssRNA_fasta
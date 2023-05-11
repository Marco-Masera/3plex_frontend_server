from token_queue_mng.models import *
from django.core.files.uploadedfile import InMemoryUploadedFile

class TriplexService:
    
    def submit_job(ssRNA_fasta: InMemoryUploadedFile, dsDNA_fasta: InMemoryUploadedFile, token: int):
        #Submit the job
        pass 
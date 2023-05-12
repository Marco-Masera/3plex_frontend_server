from .models import JobData
from triplex_frontend.triplex_exceptions import DataDoesNotExistException, TokenIsNotStateSubmittedException
from token_queue_mng.services import TokenQueueService
from token_queue_mng.models import *

class ResultsMngServices:
    def get_by_token(token: str):
        try:
            return JobData.objects.get(
                token__token = token
            )
        except JobData.DoesNotExist:
            raise DataDoesNotExistException()

    def submit_error(token: str):
        TokenQueueService.set_token_failed(token)  
        job = ResultsMngServices.get_by_token(token)
        job.delete()    

    def delete_data_by_token(token: str):
        ResultsMngServices.get_by_token(token).delete() 

    def initialize_data_section(token: str, ssRNA_fasta, ssRNA_id = None):
        #Initialize data section, keep track of sequence and id, used later for computing the conservation
        token_ = TokenQueueService.find_token(token)
        job = JobData()
        job.token = token_
        job.ssRna_fasta = ssRNA_fasta
        job.ssRna_id = ssRNA_id 
        job.ssRna_fasta.name = f"{token}/{job.ssRna_fasta.name}"
        job.save()
    
    def post_data(token: str, stability, summary):
        #Note: data must be initialized or this will return DataDoesNotExistException
        data = ResultsMngServices.get_by_token(token)
        if (not TokenQueueService.token_is_state_submitted(data.token)):
            raise TokenIsNotStateSubmittedException()
        data.stability = stability
        data.summary = summary
        data.stability.name = f"{token}/{data.stability.name}"
        data.summary.name = f"{token}/{data.summary.name}"
        data.save()
    
    def get_data_by_token(token:str):
        token = TokenQueueService.find_token(token)
        token.assert_state_ready()
        data = ResultsMngServices.get_by_token(token)
        #Returns urls of available data
        available = dict()
        if (data.ssRna_fasta != None):
            available[data.ssRna_fasta.name] = data.ssRna_fasta.url
        if (data.stability != None):
            available[data.stability.name] = data.stability.url
        if (data.summary != None):
            available[data.summary.name] = data.summary.url
        return available
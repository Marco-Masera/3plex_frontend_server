from .models import JobData
from triplex_frontend.triplex_exceptions import DataDoesNotExistException, TokenIsNotStateSubmittedException
from token_queue_mng.services import TokenQueueService
from datetime import datetime

class ResultsMngServices:
    #Retrieve data from token (string)
    def get_by_token(token: str):
        try:
            return JobData.objects.get(
                token__token = token
            )
        except JobData.DoesNotExist:
            raise DataDoesNotExistException()

    def delete_data_by_token(token: str):
        ResultsMngServices.get_by_token(token).delete() 

    def initialize_data_section(token: str, ssRNA_fasta, dsDNA_fasta, triplex_params, ssRNA_id = None):
        #Initialize data section, keep track of sequence and id, used later for computing the conservation
        token_ = TokenQueueService.find_token(token)
        job = JobData()
        job.token = token_
        job.ssRNA_id = ssRNA_id 
        job.ssRNA_fasta = ssRNA_fasta
        job.ssRNA_fasta.name = f"{token}/ssRNA.fa"
        job.dsDNA_fasta = dsDNA_fasta
        job.dsDNA_fasta.name = f"{token}/dsDNA.fa"
        job.triplex_params = triplex_params
        job.save()
    
    def save_data(token: str, stability, summary):
        #Note: data must be initialized or this will return DataDoesNotExistException
        data = ResultsMngServices.get_by_token(token)
        if (not TokenQueueService.token_is_state_submitted(data.token)):
            raise TokenIsNotStateSubmittedException()
        data.stability = stability
        data.summary = summary
        data.stability.name = f"{token}/{data.stability.name}"
        data.summary.name = f"{token}/{data.summary.name}"
        data.save()

    def update_data_last_date(token: str):
        jobData = ResultsMngServices.get_by_token(token) #TODO
        jobData.date = datetime.now()
        jobData.save()
    
    def get_data_by_token(token:str):
        TokenQueueService.assert_token_ready(token)
        data = ResultsMngServices.get_by_token(token)
        #Returns urls of available data
        available = dict()
        if (data.ssRNA_fasta != None):
            available[data.ssRNA_fasta.name] = data.ssRNA_fasta.url
        if (data.dsDNA_fasta != None):
            available[data.dsDNA_fasta.name] = data.dsDNA_fasta.url
        if (data.stability != None):
            available[data.stability.name] = data.stability.url
        if (data.summary != None):
            available[data.summary.name] = data.summary.url
        return available
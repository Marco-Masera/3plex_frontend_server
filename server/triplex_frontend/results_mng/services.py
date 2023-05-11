from .models import JobData
from triplex_frontend.triplex_exceptions import DataDoesNotExistException
from token_queue_mng.services import TokenQueueService

class ResultsMngServices:
    def get_by_token(token: int):
        try:
            return JobData.objects.get(
                token__token = token
            )
        except JobData.DoesNotExist:
            raise DataDoesNotExistException()

    def delete_data_by_token(token: int):
        ResultsMngServices.get_by_token(token).delete() 

    def initialize_data_section(token: int, ssRNA_fasta, ssRNA_id = None):
        #Initialize data section, keep track of sequence and id, used later for computing the conservation
        token_ = TokenQueueService.find_token(token)
        JobData.objects.create(
            token = token_,
            ssRna_fasta = ssRNA_fasta,
            ssRna_id = ssRNA_id
         )
    
    def post_data(token: int, stability, summary):
        #Note: data must be initialized or this will return DataDoesNotExistException
        data = ResultsMngServices.get_by_token(token)
        data.stability = stability
        data.summary = summary
        print(data.summary)
        data.save()
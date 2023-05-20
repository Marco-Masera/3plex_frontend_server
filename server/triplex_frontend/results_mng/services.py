from .models import JobData
from triplex_frontend.triplex_exceptions import DataDoesNotExistException, TokenIsNotStateSubmittedException
from token_queue_mng.services import TokenQueueService
from datetime import datetime
from django.db.models import Q
import filecmp
from results_mng.hash_lib import get_hash

class ResultsMngServices:
    #Retrieve data from token (string)
    def get_by_token(token: str):
        job = TokenQueueService.find_token(token).job
        if (job is None):
            raise DataDoesNotExistException()
        return job

    #Delete data object if no token exists associated to it (mostly for exception handling)
    def delete_data_if_orphan(jobData: JobData):
        if (len(TokenQueueService.get_tokens_by_job(jobData))==0):
            jobData.delete()

    def find_job_with_equal_input(hash_string, other_job):
        jobs = JobData.objects.filter(hash_code=hash_string).filter(Q(state="Submitted") | Q(state="Ready")).filter(triplex_params=other_job.triplex_params)
        for job in jobs:
            if (job.pk == other_job.pk):
                continue
            if (filecmp.cmp(job.ssRNA_fasta.path, other_job.ssRNA_fasta.path) and filecmp.cmp(job.dsDNA_fasta.path, other_job.dsDNA_fasta.path)):
                return job
        return None 

    def initialize_or_retrieve_data_section(ssRNA_fasta, dsDNA_fasta, triplex_params, ssRNA_id = None):
        #Compute hash value of input data
        hashed = get_hash([ssRNA_fasta,dsDNA_fasta], [triplex_params])
        #initialize new data section, keep track of sequence and id, used later for computing the conservation
        job = JobData()
        job.hash_code = hashed
        job.triplex_params = triplex_params
        job.save() #To generate id
        job.ssRNA_id = ssRNA_id 
        job.ssRNA_fasta = ssRNA_fasta
        job.ssRNA_fasta.name = f"{job.pk}/ssRNA.fa"
        job.dsDNA_fasta = dsDNA_fasta
        job.dsDNA_fasta.name = f"{job.pk}/dsDNA.fa"
        job.save()
        #Check if there is a viable job already submitted
        existingJob = ResultsMngServices.find_job_with_equal_input(hashed, job)
        if (existingJob is not None):
            print("Found job already cached")
            job.delete()
            return existingJob
        return job
    
    def receive_data(token: str, stability, summary) -> JobData:
        #Note: data must be initialized or this will return DataDoesNotExistException
        tokenObject = TokenQueueService.find_token(token)
        data = tokenObject.job

        if (not TokenQueueService.token_is_state_submitted(tokenObject)):
            raise TokenIsNotStateSubmittedException()

        data.stability = stability
        data.summary = summary
        data.stability.name = f"{data.pk}/{data.stability.name}"
        data.summary.name = f"{data.pk}/{data.summary.name}"
        data.state = "Ready"
        data.save()
        return data

    def update_data_last_date(token: str):
        jobData = ResultsMngServices.get_by_token(token)
        jobData.date = datetime.now()
        jobData.save()
    
    def get_data_by_token(token:str):
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

    
    def set_job_failed(token: str):
        jobObject = ResultsMngServices.get_by_token(token)
        jobObject.state = "Failed"
        jobObject.save()
    
    def cleanup_old_jobs(cleanup_older_than):
        old_jobs = JobData.objects.filter(date__lte=cleanup_older_than, cleaned_up = False)
        for old_job in old_jobs:
            if (old_job.state == "Ready" or old_job.state == "Created"):
                old_job.state = "Expired"
            elif (old_job.state == "Submitted"):
                old_job.state = "Cancelled"
            old_job.delete_all_files()
            old_job.cleaned_up = True
            old_job.save()

    def set_job_submitted(jobData: JobData):
        jobData.state = "Submitted"
        jobData.save()
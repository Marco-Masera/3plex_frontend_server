from .models import *
from triplex_frontend.triplex_exceptions import DataDoesNotExistException, TokenIsNotStateSubmittedException, SsRnaIdNotValidException
from token_queue_mng.services import TokenQueueService
from datetime import datetime
from django.conf import settings
from django.db.models import Q
import hmac
import os
import gzip
from django.db import transaction
from results_mng.hash_lib import get_hash
from visualization.visualization_utils import get_repeats_by_transcript_id, get_conservation_by_transcript_id

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
            #Check they are actually equal
            if (other_job.semantic_equals(job)):
                print("Cached")
                return job
        return None 

    def initialize_or_retrieve_data_section(ssRNA_fasta, dsDNA_fasta, dsDNA_precomputed, triplex_params, ssRNA_id = None, species = None, use_randomization=0):
        #Compute hash value of input data
        hashed = get_hash([ssRNA_fasta,dsDNA_fasta], [triplex_params, {"id":ssRNA_id, "species": species, "dsDNA_precomputed":dsDNA_precomputed, "randomization": use_randomization}])
        #initialize new data section, keep track of sequence and id, used later for computing the conservation
        job = JobData()
        job.hash_code = hashed
        job.triplex_params = triplex_params
        job.save() #To generate id
        if (ssRNA_id is not None):
            try:
                longestTranscript = LongestTranscript.objects.get(id=ssRNA_id)
                job.ssRNA_id = longestTranscript
            except LongestTranscript.DoesNotExist:
                raise SsRnaIdNotValidException()
        else:
            job.ssRNA_id = None
        if (ssRNA_fasta is not None):
            job.ssRNA_fasta = ssRNA_fasta
            job.ssRNA_fasta.name = f"jobs/{job.base_path}/{settings.SSRNA_BASE_NAME}"
        if (job.dsDNA_fasta is not None):
            job.dsDNA_fasta = dsDNA_fasta
            job.dsDNA_fasta.name = f"jobs/{job.base_path}/{job.dsDNA_fasta.name}"
        if (dsDNA_precomputed is not None):
            targetSites = DnaTargetSites.objects.get(name=dsDNA_precomputed)
            job.dsDNA_precomputed_target = targetSites
        job.species = species
        job.use_random = use_randomization
        job.save()
        #Check if there is a viable job already submitted
        existingJob = ResultsMngServices.find_job_with_equal_input(hashed, job)
        if (existingJob is not None):
            print("Found job already cached")
            job.delete()
            return existingJob
        return job
    
    def receive_data(token: str, stability, summary, profile, secondary_struct, profile_random, stability_indexed) -> JobData:
        #Note: data must be initialized or this will return DataDoesNotExistException
        tokenObject = TokenQueueService.find_token(token)
        data = tokenObject.job

        if (not TokenQueueService.token_is_state_submitted(tokenObject)):
            raise TokenIsNotStateSubmittedException()

        
        data.stability = stability
        data.summary = summary
        data.stability.name = f"jobs/{data.base_path}/{data.stability.name}"
        data.summary.name = f"jobs/{data.base_path}/{data.summary.name}"
        data.stability_indexed = stability_indexed
        if (stability_indexed is not None):
            data.stability_indexed.name = f"jobs/{data.base_path}/{data.stability_indexed.name}"

        data.profile = profile
        data.profile.name = f"jobs/{data.base_path}/{data.profile.name}"
        if (profile_random):
            data.profile_random = profile_random
            data.profile_random.name = f"jobs/{data.base_path}/{data.profile_random.name}"
        data.secondary_structure = secondary_struct
        data.secondary_structure.name = f"jobs/{data.base_path}/{data.secondary_structure.name}"
        data.state = "Ready"
        data.save()
        #Stability web: only if input was .bed
        build_summary_web = (stability_indexed is not None)
        if (build_summary_web):
            ResultsMngServices.build_summary_web(data)

        TokenQueueService.notify_all_users_email_job_completed(data)
        return data

    def update_data_last_date(token: str):
        jobData = ResultsMngServices.get_by_token(token)
        jobData.date = datetime.now()
        jobData.save()

    def get_data_for_visuals(token:str):
        data = ResultsMngServices.get_by_token(token)
        #Returns urls of available data
        def clean_name(name):
            return name.split("/")[-1]
        available = dict()
        #Profile for tfo count
        if (data.profile != None  and bool(data.profile)):
            available["tfo_profile"] = data.profile.url
        if (data.secondary_structure != None  and bool(data.secondary_structure)):
            available["secondary_structure"] = data.secondary_structure.url
        #Signal for conservation
        if (data.ssRNA_id):
            available["conservation"] = get_conservation_by_transcript_id(data.ssRNA_id)
            #Signal for repeats
            available["repeats"] = get_repeats_by_transcript_id(data.ssRNA_id)
        #ssRNA sequence
        if (data.ssRNA_id is not None):
            ssRNA_fasta = data.ssRNA_id.ssRNA_fasta_path
            with gzip.open(ssRNA_fasta, mode='rt') as file:
                sequence = file.read()
                sequence = ''.join(sequence.splitlines(keepends=False)[1:])
                available["sequence"] = sequence
        else:
            ssRNA_fasta = data.ssRNA_fasta.path
            with open(ssRNA_fasta, 'r') as file:
                sequence = file.read()
                sequence = ''.join(sequence.splitlines(keepends=False)[1:])
                available["sequence"] = sequence
        #Profile rand
        if (data.profile_random is not None and bool(data.profile_random)):
            available["statistics"] = data.profile_random.url
        
        return available
    
    def get_data_by_token(token:str):
        data = ResultsMngServices.get_by_token(token)
        #Returns urls of available data
        def clean_name(name):
            return name.split("/")[-1]
        available = dict()
        if (data.ssRNA_fasta != None  and bool(data.ssRNA_fasta)):
            available[clean_name(data.ssRNA_fasta.name)] = data.ssRNA_fasta.url
        elif (data.ssRNA_id != None):
            available[f"ssRNA_{data.ssRNA_id.id}"] = data.ssRNA_id.ssRNA_fasta_url
        if (data.dsDNA_fasta != None and bool(data.dsDNA_fasta) and os.path.isfile(data.dsDNA_fasta.path)):
            available[clean_name(data.dsDNA_fasta.name)] = data.dsDNA_fasta.url
        if (data.dsDNA_precomputed_target is not None):
            available[f"dsDNA_{data.dsDNA_precomputed_target.name}"] = data.dsDNA_precomputed_target.dsDNA_url
        if (data.stability != None  and bool(data.stability)):
            available[clean_name(data.stability.name)] = data.stability.url
        if (data.summary != None  and bool(data.summary)):
            available[clean_name(data.summary.name)] = data.summary.url
        if (data.rawLogsSTDERR != None and bool(data.rawLogsSTDERR)):
            available["Logs_STDERR"] = data.rawLogsSTDERR.url
        if (data.rawLogsSTDOUT != None and bool(data.rawLogsSTDOUT)):
            available["Logs_STDOUT"] = data.rawLogsSTDOUT.url
        return available

    def get_triplex_params(token:str):
        data = ResultsMngServices.get_by_token(token)
        return data.triplex_params
    
    def set_job_failed(token: str, STDOUT = None, STDERR = None):
        jobObject = ResultsMngServices.get_by_token(token)
        jobObject.state = "Failed"

        if (STDOUT is not None):
            jobObject.rawLogsSTDOUT = STDOUT
            jobObject.rawLogsSTDOUT.name = f"jobs/{jobObject.base_path}/Logs_STDOUT"
        if (STDERR is not None):
            jobObject.rawLogsSTDERR = STDERR
            jobObject.rawLogsSTDERR.name = f"jobs/{jobObject.base_path}/Logs_STDERR"

        jobObject.save()
        TokenQueueService.notify_all_users_email_job_failed(jobObject)
    
    def cleanup_old_jobs(cleanup_older_than):
        old_jobs = JobData.objects.filter(date__lte=cleanup_older_than, cleaned_up = False)
        for old_job in old_jobs:
            old_job.state = "Expired"
            old_job.delete_all_files()
            old_job.cleaned_up = True
            old_job.save()

    def set_job_submitted(jobData: JobData):
        jobData.state = "Submitted"
        jobData.save()

    def check_token_hmac(token, hashed):
        h = hmac.new(bytes(settings.HMAC_KEY, 'utf-8'), msg=bytes(token, 'utf-8'), digestmod='sha256')
        digested = h.hexdigest()
        return hmac.compare_digest(digested, hashed)

    def search_longest_transcripts(query, species, max_elems = 20):
        if (max_elems != None):
            max_elems = int(max_elems)
            return LongestTranscript.objects.filter(species=species).filter(Q(gene_id__istartswith=query) | Q(id__istartswith=query) | Q(gene_name__istartswith=query)).order_by('-longest')[:max_elems]
        
        return LongestTranscript.objects.filter(Q(gene_id__istartswith=query) | Q(id__istartswith=query) | Q(gene_name__istartswith=query)).order_by('-longest')

    def get_dna_target_sites():
        return DnaTargetSites.objects.all()

    @transaction.atomic
    def build_summary_web(jobData: JobData):
        with gzip.open(jobData.summary.path, mode='rt') as summary_file:
            for line in summary_file.readlines()[1:]:
                line = line.split("\t")
                summary = SummaryWebVersion()
                summary.job = jobData
                summary.ssRNA_id = line[1]
                summary.dsDNA_id = line[0]
                seqId = line[0].split(":")
                summary.dsDNA_chr = seqId[2]
                coords = seqId[3].split("-")
                summary.dsDNA_b = coords[0]
                summary.dsDNA_e = coords[1]
                summary.stability_best = float(line[11])
                summary.stability_norm = float(line[14])
                summary.score_best = float(line[13])
                summary.save()
    
    def get_web_summary(jobData: JobData):
        return SummaryWebVersion.objects.filter(job=jobData)

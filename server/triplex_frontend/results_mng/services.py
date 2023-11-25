from .models import *
from triplex_frontend.triplex_exceptions import DataDoesNotExistException, TokenIsNotStateSubmittedException, SsRnaIdNotValidException
from token_queue_mng.services import TokenQueueService
from datetime import datetime
from django.conf import settings
from django.db.models import Q
import hmac
import os
import gzip
import tempfile
import subprocess
from django.db import transaction
from results_mng.hash_lib import get_hash
from visualization.visualization_utils import get_repeats_by_transcript_id, get_conservation_by_transcript_id
import sqlite3
from results_mng.tfo_profile import compute_profile_from_tpx, compute_profile_for_genome_browser

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

    def initialize_or_retrieve_data_section(ssRNA_fasta, dsDNA_fasta, dsDNA_precomputed, triplex_params, ssRNA_id = None, species = None, use_randomization=0, is_bed = False):
        #Compute hash value of input data
        hashed = get_hash([ssRNA_fasta,dsDNA_fasta], [triplex_params, {"id":ssRNA_id, "species": species, "dsDNA_precomputed":dsDNA_precomputed, "randomization": use_randomization}])
        
        #If user provided bed file or dsDNA precomputed, then a bed file is available for the system
        is_bed = is_bed or dsDNA_precomputed is not None
    
        #initialize new data section, keep track of sequence and id, used later for computing the conservation
        job = JobData()
        job.is_dsDNA_bed = is_bed
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
    
    def receive_data(token: str, stability, summary, profile, secondary_struct, profile_random) -> JobData:
        #Note: data must be initialized or this will return DataDoesNotExistException
        tokenObject = TokenQueueService.find_token(token)
        data = tokenObject.job

        if (not TokenQueueService.token_is_state_submitted(tokenObject)):
            raise TokenIsNotStateSubmittedException()

        
        data.stability = stability
        data.summary = summary
        data.stability.name = f"jobs/{data.base_path}/{data.stability.name}"
        data.summary.name = f"jobs/{data.base_path}/{data.summary.name}"

        data.profile = profile
        data.profile.name = f"jobs/{data.base_path}/{data.profile.name}"
        if (profile_random):
            data.profile_random = profile_random
            data.profile_random.name = f"jobs/{data.base_path}/{data.profile_random.name}"
        data.secondary_structure = secondary_struct
        data.secondary_structure.name = f"jobs/{data.base_path}/{data.secondary_structure.name}"
        data.save()
        stability_indexed = ResultsMngServices.build_stabilty_indexed(data)
        print(stability_indexed)
        data.stability_indexed.name = stability_indexed
        data.state = "Ready"
        data.save()
        #Stability web: only if input was .bed
        build_summary_web = data.is_dsDNA_bed
        if (build_summary_web):
            ResultsMngServices.build_summary_web(data)

        TokenQueueService.notify_all_users_email_job_completed(data)
        return data

    def update_data_last_date(token: str):
        jobData = ResultsMngServices.get_by_token(token)
        jobData.date = datetime.now()
        jobData.save()

    def get_data_for_visuals(token:str, dsDNA_id = None):
        data = ResultsMngServices.get_by_token(token)
        #Returns urls of available data
        def clean_name(name):
            return name.split("/")[-1]
        available = dict()
        #Profile for tfo count
        if (dsDNA_id is None):
            if (data.profile != None  and bool(data.profile)):
                available["tfo_profile"] = data.profile.url
                available["profile_dynamic"] = False
        else:
            available["tpx"] = ResultsMngServices.get_tpx_by_dsDNAID(data, dsDNA_id)
            available["tfo_profile"] = f"jobs/{token}/{dsDNA_id}/profile"
            available["profile_dynamic"] = True
            
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
        if (data.profile_random is not None and bool(data.profile_random) and dsDNA_id is None):
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

    
    def build_stabilty_indexed(data: JobData):
        is_bed_file = data.is_dsDNA_bed
        path = f"jobs/{data.base_path}/index_tpx_stability.db"
        full_path = os.path.join(settings.MEDIA_ROOT, path)
        print(full_path)
        conn = sqlite3.connect(full_path)
        cursor = conn.cursor()
        # Create the table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS TPX_Stability (id INTEGER PRIMARY KEY AUTOINCREMENT,
                tfo_start INTEGER, tfo_end INTEGER,
                Duplex_ID TEXT, TTS_start INTEGER,
                TTS_end INTEGER, Score REAL,
                Error_rate REAL, Errors TEXT,
                Motif TEXT, Strand TEXT,
                Orientation TEXT, Guanine_rate REAL,
                Stability REAL, Representation TEXT)''')

        conn.commit()
        with gzip.open(data.stability.path, mode='rt') as stability:
            for line_ in stability.readlines()[1:]:
                line = line_.split("\t")
                tfo_start = int(line[1])
                tfo_end = int(line[2])
                Duplex_ID = line[3]
                if (is_bed_file):
                    chr_start = int(Duplex_ID.split(":")[-1].split("-")[0])
                else:
                    chr_start = 0
                TTS_start = int(line[4])+chr_start
                TTS_end = int(line[5])+chr_start
                Score = float(line[6])
                Error_rate = float(line[7])
                Errors = line[8]
                Motif = line[9]
                Strand = line[10]
                Orientation = line[11]
                Guanine_rate = float(line[12])
                Stability = float(line[13])
                #Build tfo string representation
                tfo_tts = f"{line[14]}\n{line[15]}\n{line[16]}\n{line[17]}"
                # Save the object to the database
                cursor.execute('''
                    INSERT INTO TPX_Stability
                    (tfo_start, tfo_end, Duplex_ID, TTS_start, TTS_end, Score, Error_rate, Errors, Motif, Strand, Orientation, Guanine_rate, Stability, Representation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (tfo_start, tfo_end, Duplex_ID, TTS_start, TTS_end,
                    Score, Error_rate, Errors, Motif, Strand, Orientation,
                    Guanine_rate, Stability, tfo_tts))

        conn.commit()
        conn.close()
        return path

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
        if (jobData.is_dsDNA_bed == False):
            return None
        return SummaryWebVersion.objects.filter(job=jobData)

    def get_trace_for_genome_browser(job, dsDNA_id, min_stability):
        def build_url(obj):
            #Build URL
            species = settings.SPECIES_NAMES_TO_UCSC[obj.job.species]
            trace_url = f'https://www.3plex.unito.it{obj.file.url}'.replace("debug/", "")
            url = f"http://genome.ucsc.edu/cgi-bin/hgTracks?org={species}&hgt.customText={trace_url}"
            return url

        if not (os.path.isfile(job.stability_indexed.path)):
            return []
        #Check if there is a temp file already set
        file = JobUCSCTrack.objects.filter(job=job,dsDNA_id=dsDNA_id,stability=str(min_stability)).first()
        if (file is not None):
            return build_url(file)
        conn = sqlite3.connect(job.stability_indexed.path)
        cursor = conn.cursor()
        query = """
            SELECT TTS_start, TTS_end, Stability FROM TPX_Stability
            WHERE Duplex_ID = ? AND Stability >= ?;
        """
        cursor.execute(query, (dsDNA_id , min_stability))
        # Fetch all the records that satisfy the conditions
        tpx = cursor.fetchall()
        conn.close()

        #Build file
        #If too many temp files, delete one
        files = JobUCSCTrack.objects.filter(job=job)
        if (files.count() >= settings.MAX_TEMP_FILES):
            files[0].delete()
        
        #Create JobUCSCTrack object
        obj = JobUCSCTrack()
        obj.job = job; obj.stability = str(min_stability); obj.dsDNA_id = dsDNA_id
        file_path = f"jobs/{job.base_path}/tmp{dsDNA_id}_{str(min_stability)}"
        full_file_path = os.path.join(settings.MEDIA_ROOT, file_path)

        chr_ = dsDNA_id.split(":")[2]
        trace_name = f"tpx count in {dsDNA_id}"
        TIME = datetime.now()
        values, min_, max_ = compute_profile_for_genome_browser(tpx, chr_)
        print(f"Len values: {len(values)}")
        print(f"Took {datetime.now() - TIME}")
        header = f"""browser position {chr_}:{min_}-{max_}
browser hide all
browser pack refGene encodeRegions
browser full altGraph
#	300 base wide bar graph, autoScale is on by default == graphing
#	limits will dynamically change to always show full range of data
#	in viewing window, priority = 20 positions this as the second graph
#	Note, zero-relative, half-open coordinate system in use for bedGraph format
track type=bedGraph name="{trace_name}" description="Number of tpx with stability >= {min_stability}" visibility=full color=200,100,0 altColor=0,100,200 priority=20
"""
        with open(full_file_path, "w") as file:
            file.write(header)
            for string in values:
                file.write(string)
        obj.file.name = file_path
        obj.save()
        return build_url(obj)
         


    def get_profile_dsDNAID(job, dsDNAID):
        if not (os.path.isfile(job.stability_indexed.path)):
            return []
        conn = sqlite3.connect(job.stability_indexed.path)
        cursor = conn.cursor()
        query = """
            SELECT tfo_start, tfo_end, Stability FROM TPX_Stability
            WHERE Duplex_ID = ? ORDER BY Stability DESC;
        """
        cursor.execute(query, (dsDNAID ,))
        # Fetch all the records that satisfy the conditions
        tpx = cursor.fetchall()
        conn.close()
        return compute_profile_from_tpx(tpx)

    def get_tpx_by_dsDNAID(data, dsDNA_id):
        def dict_factory(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d
        if not (os.path.isfile(data.stability_indexed.path)):
            return []
        conn = sqlite3.connect(data.stability_indexed.path)
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        query = """
            SELECT * FROM TPX_Stability
            WHERE Duplex_ID = ?
        """
        cursor.execute(query, (dsDNA_id ,))
        # Fetch all the records that satisfy the conditions
        records = cursor.fetchall()
        conn.close()
        return records
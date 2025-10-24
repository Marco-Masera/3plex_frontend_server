from .models import *
from triplex_frontend.triplex_exceptions import DataDoesNotExistException, TokenIsNotStateSubmittedException, SsRnaIdNotValidException
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
import sqlite3

class ResultsMngServices:

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

    def initialize_or_retrieve_data_section(ssRNA_fasta, dsDNA_fasta, dsDNA_precomputed, triplex_params, 
    ssRNA_id = None, species = None, use_randomization=0, is_bed = False):
        
        #If user provided bed file or dsDNA precomputed, then a bed file is available for the system
        is_bed = is_bed or dsDNA_precomputed is not None

        #Compute hash value of input data
        triplex_params_stringified = {}
        for k in triplex_params.keys():
            triplex_params_stringified[k] = str(triplex_params[k])
        hashed = get_hash([ssRNA_fasta,dsDNA_fasta], [triplex_params_stringified, {"id":ssRNA_id, "species": species, "dsDNA_precomputed":dsDNA_precomputed, "randomization": use_randomization}])
    
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
    
    def receive_data(data: JobData, stability, summary, profile, secondary_struct, profile_random) -> JobData:
        #Set file fields        
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
        #Need to index tpx.stability
        stability_size = os.path.getsize(data.stability.path)
        if (stability_size < 500000000):  # 500 MB
            stability_indexed = ResultsMngServices.build_stabilty_indexed(data)
            data.stability_indexed.name = stability_indexed
        else:
            #If the file is too big, we do not index it
            data.stability_indexed = None
        #Set state Ready
        data.state = "Ready"
        data.save()
        #If input was .bed index tpx.summary too
        build_summary_web = data.is_dsDNA_bed
        if (build_summary_web):
            path = ResultsMngServices.build_summary_web(data)
            data.summary_web.name = path
            data.save()

        return data

    def update_data_last_date(jobData: JobData):
        jobData.date = datetime.now()
        jobData.save()


    def get_data(data: JobData):
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

    def get_triplex_params(job: JobData):
        return job.triplex_params
    
    def set_job_failed(jobObject: JobData, STDOUT = None, STDERR = None):
        jobObject.state = "Failed"

        if (STDOUT is not None):
            jobObject.rawLogsSTDOUT = STDOUT
            jobObject.rawLogsSTDOUT.name = f"jobs/{jobObject.base_path}/Logs_STDOUT"
        if (STDERR is not None):
            jobObject.rawLogsSTDERR = STDERR
            jobObject.rawLogsSTDERR.name = f"jobs/{jobObject.base_path}/Logs_STDERR"

        jobObject.save()
    
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
            next(stability) #Skip header
            for line_ in stability:
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
            path = f"jobs/{jobData.base_path}/summary_web.db"
            full_path = os.path.join(settings.MEDIA_ROOT, path)
            conn = sqlite3.connect(full_path)
            cursor = conn.cursor()
            # Create the table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Summary_Web (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ssRNA_id TEXT, dsDNA_id TEXT, dsDNA_chr TEXT,
                    dsDNA_b INTEGER, dsDNA_e INTEGER, stability_best REAL,
                    stability_norm REAL, score_best REAL)''')

            next(summary_file) #Skip header
            for line in summary_file:
                line = line.split("\t")
                seqId = line[0].split(":")#not in db
                coords = seqId[3].split("-")#not in db

                ssRNA_id = line[1]
                dsDNA_id = line[0]
                dsDNA_chr = seqId[2]
                dsDNA_b = coords[0]
                dsDNA_e = coords[1]
                stability_best = float(line[11])
                stability_norm = float(line[14])
                score_best = float(line[13])
                cursor.execute('''
                    INSERT INTO Summary_Web
                    (ssRNA_id, dsDNA_id, dsDNA_chr,dsDNA_b, dsDNA_e, stability_best,stability_norm, score_best)
                    VALUES (?,?,?,?,?,?,?,?)
                ''', (ssRNA_id, dsDNA_id, dsDNA_chr,dsDNA_b, dsDNA_e, stability_best,stability_norm, score_best))

            conn.commit()
            conn.close()
            return path
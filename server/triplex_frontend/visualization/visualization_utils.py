#!/usr/bin/env python
#import genomeToTranscriptMapper as gttm
import pyBigWig
from django.conf import settings
from results_mng.models import *
import numpy as np
from os import path
from visualization import genomeToTranscriptMapper as gttm
import sqlite3
from datetime import datetime
import gzip
import xlsxwriter
from visualization.tfo_profile import compute_profile_from_tpx, compute_profile_for_genome_browser
from io import BytesIO
from triplex_frontend.triplex_exceptions import TPXNotFound

def genomic_intervalsToTranscript(exons, bb, strand):
    repeats = []
    intervals = []
    converted = []
    for exon in exons:
        repeats_intersected = bb.entries(exon.chr, exon.start, exon.end)
        if (repeats_intersected is not None):
            repeats.append(repeats_intersected)
            intervals.append((exon.start, exon.end))
    if (len(intervals)==0):
        return []
    converter = gttm.GenomeToTranscriptMapper(intervals, strand)

    for repeats_block in repeats:
        for line in repeats_block:
            b = int(line[0])
            e = int(line[1])
            transcript_coords = converter.convert_interval_genome_to_transcript(b,e)
            converted.append((transcript_coords[0], transcript_coords[1], line[2].split("\t")[0]))
    return converted


def get_conservation_by_transcript_id(transcript):
    transcript_id = transcript.id
    species = transcript.species
    conservation_bw = f"{settings.MEDIA_ROOT}/static_data/{species}/conservation.bw"

    exons = TranscriptExon.objects.filter(transcript_id=transcript_id).order_by('start')
    if (not exons or len(exons)==0):
        return []

    strand = exons[0].strand
    signal = []
    full_signal = pyBigWig.open(conservation_bw)

    for exon in exons:
        signal.extend(full_signal.values(exon.chr, exon.start, exon.end))

    if(strand=="-"):
        signal.reverse()
    return signal

def get_repeats_by_transcript_id(transcript):
    transcript_id = transcript.id
    species = transcript.species
    exons = TranscriptExon.objects.filter(transcript_id=transcript_id).order_by('start')
    if (not exons or len(exons)==0):
        return []
    repeats_file =  f"{settings.MEDIA_ROOT}/static_data/{species}/repeats.bb"
    repeats_file = pyBigWig.open(repeats_file)
    return genomic_intervalsToTranscript(exons, repeats_file, exons[0].strand)


class VisualizationUtils:

    def get_tpx_by_dsDNAID(data, dsDNA_id, stability=None):
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
        if (stability is None):
            query = """
                SELECT * FROM TPX_Stability
                WHERE Duplex_ID = ?
            """
            cursor.execute(query, (dsDNA_id ,))
        else:
            query = """
                SELECT * FROM TPX_Stability
                WHERE Duplex_ID = ? AND Stability >= ?
            """
            cursor.execute(query, (dsDNA_id , stability))
        # Fetch all the records that satisfy the conditions
        records = cursor.fetchall()
        conn.close()
        return records

    def export_tpx_in_excel(tpx):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()


        for row, element in enumerate(tpx):
            to_exp = [element['Duplex_ID'], element['tfo_start'], element['tfo_end'], element['TTS_start'], element['TTS_end'], 
            element['Error_rate'], element['Errors'],element['Guanine_rate'],element['Motif'],element['Orientation'],
            element['Score'], element['Stability'], element['Strand'], element['Representation']]
            for column, elem in enumerate(to_exp):
                worksheet.write(row, column, elem)
        workbook.close()
        return output.getvalue()

    def get_data_for_visuals(data, token, dsDNA_id = None):
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
            available["tpx"] = VisualizationUtils.get_tpx_by_dsDNAID(data, dsDNA_id)
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

    def get_web_summary(jobData: JobData):
        def dict_factory(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d
        if (jobData.is_dsDNA_bed == False):
            return None
        to_return = []
        #Open sqlite file 
        #Check if there is a temp file already set
        if jobData.summary_web is None or not os.path.isfile(jobData.summary_web.path):
            return []
        conn = sqlite3.connect(jobData.summary_web.path)
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        query = """
            SELECT ssRNA_id, dsDNA_id, dsDNA_chr,dsDNA_b, dsDNA_e, stability_best,stability_norm, score_best FROM Summary_Web;
        """
        cursor.execute(query)
        summary = cursor.fetchall()
        conn.close()
        return summary

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
        header = f"""browser position {chr_}:{min_}-{max_}
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

    def find_tpx_in_interval(data, start, end, stability_th, dsDNA_id=None):
        def dict_factory(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d
        if not (path.isfile(data.stability_indexed.path)):
            return None
        conn = sqlite3.connect(data.stability_indexed.path)
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        if (dsDNA_id is None):
            query = """
            SELECT * FROM TPX_Stability
            WHERE Stability >= ? AND tfo_start <= ? AND tfo_end >= ?
            """
            cursor.execute(query, (stability_th, end, start))
        else:
            query = """
            SELECT * FROM TPX_Stability
            WHERE Stability >= ? AND tfo_start <= ? AND tfo_end >= ? AND Duplex_ID = ?
            """
            cursor.execute(query, (stability_th, end, start, dsDNA_id))
        # Fetch all the records that satisfy the conditions
        records = cursor.fetchall()
        conn.close()
        return records


    
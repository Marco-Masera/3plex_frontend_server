#!/usr/bin/env python
#import genomeToTranscriptMapper as gttm
import pyBigWig
from django.conf import settings
from results_mng.models import TranscriptExon
import numpy as np
from os import path
from visualization import genomeToTranscriptMapper as gttm
import sqlite3
from datetime import datetime

"""
    Timing test for conservation:
        Load exons: --- 0.0019123554229736328 seconds ---
        Load bw: --- 0.0004329681396484375 seconds ---
        Produce result: --- 0.002649068832397461 seconds ---
"""

""".META: *.tpx.stability.gz *.tpx.stability
	1	ssRNA
	2	TFO_start
	3	TFO_end
	4	Duplex_ID
	5	TTS_start
	6	TTS_end
	7	Score
	8	Error_rate
	9	Errors
	10	Motif
	11	Strand
	12	Orientation
	13	Guanine_rate
	14	Stability"""



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
        WHERE Stability >= ? AND tfo_start >= ? AND tfo_end <= ?
        """
        cursor.execute(query, (stability_th, start, end))
    else:
        query = """
        SELECT * FROM TPX_Stability
        WHERE Stability >= ? AND tfo_start >= ? AND tfo_end <= ? AND Duplex_ID = ?
        """
        cursor.execute(query, (stability_th, start, end, dsDNA_id))
    # Fetch all the records that satisfy the conditions
    records = cursor.fetchall()
    conn.close()
    return records

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
    print(f"Len intervals: {len(intervals)}")
    converter = gttm.GenomeToTranscriptMapper(intervals, strand)

    for repeats_block in repeats:
        for line in repeats_block:
            b = int(line[0])
            e = int(line[1])
            transcript_coords = converter.convert_interval_genome_to_transcript(b,e)
            converted.append((transcript_coords[0], transcript_coords[1], line[2].split("\t")[0]))
    return converted

def get_repeats_by_transcript_id(transcript):
    transcript_id = transcript.id
    species = transcript.species
    exons = TranscriptExon.objects.filter(transcript_id=transcript_id).order_by('start')
    if (not exons or len(exons)==0):
        return []
    repeats_file =  f"{settings.MEDIA_ROOT}/static_data/{species}/repeats.bb"
    repeats_file = pyBigWig.open(repeats_file)
    return genomic_intervalsToTranscript(exons, repeats_file, exons[0].strand)


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


#!/usr/bin/env python

import MySQLdb
import csv
from optparse import OptionParser
from sys import argv

DB_HOST = "127.0.0.1"
DB_PORT = 30001
DB_USER = "root"
DB_PSW = "triplex"
DB_NAME = "triplex"
DB_TAB_NAME = 'results_mng_transcriptexon'


def load_data_to_db(exons_list):
    #Load transcripts into memory data structure
    transcripts = {}
    # Open database connection
    db = MySQLdb.connect(host=DB_HOST, port= DB_PORT, user=DB_USER, password=DB_PSW, database=DB_NAME)
    # prepare a cursor object using cursor() method
    cursor = db.cursor()

    with open(exons_list, "rt", encoding='ascii') as transcripts_bed:
        read = csv.reader(transcripts_bed, delimiter='\t')
        for row in read: 
            sql = f"INSERT INTO {DB_TAB_NAME}(chr, start, end, transcript_id_id, strand) VALUES (%s, %s, %s, %s, %s);"   
            
            cursor.execute(sql, (row[0], row[1], row[2], row[3].split(".")[0], row[5]))

    # Commit your changes in the database
    db.commit()
    # disconnect from server
    db.close()

def main():
    usage = "%prog EXONS_LIST.bed"
    parser = OptionParser(usage=usage)
    options, args = parser.parse_args()
    if len(args) != 1:
        exit('Unexpected argument number.')
	
    load_data_to_db(args[0])


if __name__ == '__main__': main()

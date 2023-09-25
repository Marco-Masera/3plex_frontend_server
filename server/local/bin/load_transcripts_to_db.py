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
DB_TAB_NAME = 'results_mng_longesttranscript'


def load_data_to_db(transcripts_bed_path, species):
    #Load transcripts into memory data structure
    transcripts = {}
    # Open database connection
    db = MySQLdb.connect(host=DB_HOST, port= DB_PORT, user=DB_USER, password=DB_PSW, database=DB_NAME)
    # prepare a cursor object using cursor() method
    cursor = db.cursor()
    with open(transcripts_bed_path, "rt", encoding='ascii') as transcripts_bed:
        read = csv.reader(transcripts_bed, delimiter='\t')
        for row in read: 
            sql = f"INSERT INTO {DB_TAB_NAME}(id, gene_id, gene_name, chromosome, strand, transcript_type, longest, species) VALUES (%s, %s, %s, %s, %s, %s, %s, '{species}');"   
            cursor.execute(sql, (row[0], row[1], row[2], row[3], row[4], row[5], row[6]))

    # Commit your changes in the database
    db.commit()
    # disconnect from server
    db.close()

def main():
    usage = "%prog TRANSCRIPT_LIST.bed SPECIES"
    parser = OptionParser(usage=usage)
    options, args = parser.parse_args()
    if len(args) != 2:
        exit('Unexpected argument number.')
	
    load_data_to_db(args[0], args[1])


if __name__ == '__main__': main()

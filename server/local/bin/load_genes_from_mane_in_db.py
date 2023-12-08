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
DB_TAB_NAME = 'results_mng_geneindnatargetsite'


def load_data_to_db(genes_list, MANE_pk):
    #Load transcripts into memory data structure
    genes = []
    # Open database connection
    db = MySQLdb.connect(host=DB_HOST, port= DB_PORT, user=DB_USER, password=DB_PSW, database=DB_NAME)
    # prepare a cursor object using cursor() method
    cursor = db.cursor()

    with open(genes_list, "rt", encoding='ascii') as fasta:
        for line in fasta.readlines():
            if (line.startswith(">")):
                gene = line.split(":")[0][1:]
                genes.append(gene)
    for gene in genes: 
        sql = f"INSERT INTO {DB_TAB_NAME}(target_id, name) VALUES (%s, %s);"   
        cursor.execute(sql, (MANE_pk, gene))

    # Commit your changes in the database
    db.commit()
    # disconnect from server
    db.close()

def main():
    usage = "%prog MANE.fa PK_for_mane_in_db"
    parser = OptionParser(usage=usage)
    options, args = parser.parse_args()
    if len(args) != 2:
        exit('Unexpected argument number.')
	
    load_data_to_db(args[0], args[1])


if __name__ == '__main__': main()

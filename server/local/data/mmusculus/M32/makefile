GENCODE_REFENRECE_DATA=$(BIOINFO_REFERENCE_ROOT)/gencode/dataset/mmusculus/M32/


transcripts: /home/reference_data/bioinfotree/task/gencode/dataset/mmusculus/M32/basic.annotation.exon.longest_or_not.ensg.bed
	bawk '{print $$4,$$10,$$8,$$1,$$6,$$7,$$9}' $< | perl -lane 'BEGIN{$$,="\t"} $$F[0]=~s/\.\d+$$//; $$F[1]=~s/\.\d+$$//; print @F' | bsort | uniq > $@

.META: transcripts
	1	transcript_id	ENST00000456328.2
	2	gene_id		ENSG00000290825.1
	3	gnen_name	DDX11L2
	4	chromosome	chr1
	5	stand		+
	6	transcript_type	lncRNA
	7	transcripts_is_longest


#####################################################

load_transcripts_to_db: transcripts
	load_transcripts_to_db.py transcripts "mmusculus"

load_transcripts_fasta_to_media_root: $(BIOINFO_REFERENCE_ROOT)/gencode/dataset/mmusculus/M32/transcripts_fasta_dir
	cp -a $(BIOINFO_REFERENCE_ROOT)/gencode/dataset/mmusculus/M32/transcripts_fasta_dir/. ${MEDIA_ROOT}/transcripts/mmusculus/

basic.annotation.exon.bed: $(BIOINFO_REFERENCE_ROOT)/gencode/dataset/mmusculus/M32/basic.annotation.exon.bed
	cp $(BIOINFO_REFERENCE_ROOT)/gencode/dataset/mmusculus/M32/basic.annotation.exon.bed .

load_exons_to_db: basic.annotation.exon.bed
	load_exons_to_db.py basic.annotation.exon.bed


#Repeats:
# Bed file containing the repeats
repeat_rmsk.clean_chr.bed.gz: $(GENCODE_REFENRECE_DATA)repeat_rmsk.clean_chr.bed.gz
	cp $< $@
repeat_rmsk.clean_chr.sorted.bed: repeat_rmsk.clean_chr.bed.gz
	zcat repeat_rmsk.clean_chr.bed.gz | bedtools sort > repeat_rmsk.clean_chr.sorted.bed

repeat_rmsk.clean_chr.sorted.noscore.bed: repeat_rmsk.clean_chr.sorted.bed	
	awk '{OFS="\t"; $$5=0; print}' repeat_rmsk.clean_chr.sorted.bed > repeat_rmsk.clean_chr.sorted.noscore.bed

repeat_rmsk.clean_chr.sorted.noscore.bb: repeat_rmsk.clean_chr.sorted.noscore.bed $(GENCODE_REFENRECE_DATA)ucsc_mm10.chrom.sizes
	bedToBigBed repeat_rmsk.clean_chr.sorted.noscore.bed $(GENCODE_REFENRECE_DATA)ucsc_mm10.chrom.sizes repeat_rmsk.clean_chr.sorted.noscore.bb

load_repeats_in_server: repeat_rmsk.clean_chr.sorted.noscore.bb
	cp repeat_rmsk.clean_chr.sorted.noscore.bb ${MEDIA_ROOT}/static_data/mmusculus/repeats.bb


#Conservation:
phastCons30way.bw: $(GENCODE_REFENRECE_DATA)/phastCons30way.bw
	cp $< $@
load_conservation_in_server: phastCons30way.bw
	cp phastCons30way.bw ${MEDIA_ROOT}/static_data/mmusculus/conservation.bw

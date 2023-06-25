from django.db import models
from django.dispatch import receiver
from django.conf import settings
import secrets 
import os
import filecmp
from django.db import IntegrityError

ALLOWED_SPECIES = settings.ALLOWED_SPECIES

def generate_random_alphanumeric(length) -> str:
    return secrets.token_urlsafe(length).replace("/","_").replace(" ", "").replace("\t", "")
def safe_file_cmp(file_1, file_2):
    if (bool(file_1) and bool(file_2) and os.path.isfile(file_2.path) and os.path.isfile(file_1.path)):
        return filecmp.cmp(file_1.path, file_2.path)
    else:
        return file_1 == file_2


class DnaTargetSites(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    filename = models.CharField(max_length=128, null=False, blank=False)
    description = models.CharField(max_length=256, null=True, default=None)
    external_ref = models.CharField(max_length=256, null=True, default=None)
    n_sequences = models.IntegerField()
    total_size_KB = models.IntegerField()
    species = models.CharField(max_length=32, null=False, blank=False, choices=ALLOWED_SPECIES)
    version = models.IntegerField(null=False, blank=False)

    @property
    def dsDNA_path(self):
        return f"{settings.MEDIA_ROOT_ABS_PATH}/ds_dna/{self.species}/{self.filename}"
    @property
    def dsDNA_url(self):
        return f"/3plex/results/ds_dna/{self.species}/{self.filename}"



class LongestTranscript(models.Model):
    id = models.CharField(max_length=256, primary_key=True, unique=True, null=False, blank=False)
    chromosome = models.SlugField(max_length=10, null=False, blank=False)
    strand = models.SlugField(max_length=2, null=False, blank=False)
    transcript_type = models.SlugField(max_length=64, null=False, blank=False)
    longest = models.BooleanField()
    gene_name = models.SlugField(max_length=32, null=False, blank=False)
    gene_id = models.SlugField(max_length=32, null=False, blank=False)

    species = models.CharField(max_length=32, null=False, blank=False, choices=ALLOWED_SPECIES)

    @property
    def ssRNA_fasta_path(self):
        return f"{settings.MEDIA_ROOT_ABS_PATH}/transcripts/{self.species}/{self.id.split('.')[0]}.fa.gz"
    @property
    def ssRNA_fasta_url(self):
        return f"/3plex/results/transcripts/{self.species}/{self.id.split('.')[0]}.fa.gz"

    def to_dict(self):
        return {
            'id': self.id,
            'chromosome': self.chromosome,
            'strand': self.strand,
            'transcript_type': self.transcript_type,
            'gene_name': self.gene_name,
            'gene_id': self.gene_id,
            'longest': self.longest
        }

class TranscriptExon(models.Model):
    transcript_id = models.ForeignKey(LongestTranscript, on_delete=models.CASCADE)
    chr = models.CharField(max_length=16)
    start = models.IntegerField(null=False, blank=False)
    end = models.IntegerField(null=False, blank=False)
    strand = models.CharField(max_length=1)


state_choices = [
        ("Created", "Created"),
        ("Submitted","Submitted"),
        ("Ready", "Ready"),
        ("Expired", "Expired"),
        ("Cancelled","Cancelled"),
        ("Failed","Failed")
]

class JobData(models.Model):
    #Tells django to index hash_code field for faster lookup
    class Meta:
        indexes = [models.Index(fields=['hash_code']),]

    state = models.CharField(max_length=16, choices = state_choices, default = "Created")
    hash_code = models.CharField(max_length=128)

    date = models.DateTimeField(auto_now_add=True, auto_now=False)
    triplex_params = models.JSONField()
    
    base_path = models.CharField(max_length=64, blank=False, unique=True)

    ssRNA_id = models.ForeignKey(LongestTranscript, on_delete=models.PROTECT, default=None, null=True)
    ssRNA_fasta = models.FileField(default=None, null=True)

    dsDNA_fasta = models.FileField(default=None, null=True)
    dsDNA_precomputed_target = models.ForeignKey(DnaTargetSites, null=True, default=None, on_delete=models.PROTECT)

    stability = models.FileField(default=None, null=True)
    summary = models.FileField(default=None, null=True)
    profile = models.FileField(default=None, null=True)
    secondary_structure = models.FileField(default=None, null=True)
    rawLogsSTDOUT = models.FileField(default=None, null=True)
    rawLogsSTDERR = models.FileField(default=None, null=True)

    #Cleaned up keep tracks of the job history, if it was cleaned up after not being accessed for some time
    cleaned_up = models.BooleanField(default=False)

    def semantic_equals(self, other_job):
        #Returns true if the 2 jobs are semantically equals
        return (
            #Check equality of dsDNA_fasta files
            safe_file_cmp(self.dsDNA_fasta, other_job.dsDNA_fasta) 
            #Check equality of ssRNA_fasta or ssRNA_id
            and (
                (self.ssRNA_id is not None and other_job.ssRNA_id is not None and self.ssRNA_id==other_job.ssRNA_id) 
                or (safe_file_cmp(job.ssRNA_fasta, other_job.ssRNA_fasta)))
            #Check equality of species 
            and (job.species == other.species)
            #Check equality of dsDNA_precomputed_target
            and (job.dsDNA_precomputed_target == other_job.dsDNA_precomputed_target)
            )

    def __str__(self):
        return f"{self.date} - {self.state}"

    def delete_all_files(self):
        dir_ = None
        if self.ssRNA_fasta:
            if os.path.isfile(self.ssRNA_fasta.path):
                dir_ = self.ssRNA_fasta.path
                os.remove(self.ssRNA_fasta.path)
        if self.dsDNA_fasta:
            if os.path.isfile(self.dsDNA_fasta.path):
                dir_ = self.dsDNA_fasta.path
                os.remove(self.dsDNA_fasta.path)
        if self.stability:
            if os.path.isfile(self.stability.path):
                dir_ = self.stability.path
                os.remove(self.stability.path)
        if self.summary:
            if os.path.isfile(self.summary.path):
                dir_ = self.summary.path
                os.remove(self.summary.path)
        if self.rawLogsSTDOUT:
            if os.path.isfile(self.rawLogsSTDOUT.path):
                dir_ = self.rawLogsSTDOUT.path
                os.remove(self.rawLogsSTDOUT.path)
        if self.rawLogsSTDERR:
            if os.path.isfile(self.rawLogsSTDERR.path):
                dir_ = self.rawLogsSTDERR.path
                os.remove(self.rawLogsSTDERR.path)
        if self.profile and self.profile.path:
            if os.path.isfile(self.profile.path):
                dir_ = self.profile.path
                os.remove(self.profile.path)
        if self.secondary_structure and self.secondary_structure.path:
            if os.path.isfile(self.secondary_structure.path):
                dir_ = self.secondary_structure.path
                os.remove(self.secondary_structure.path)
        if (dir_ is not None and len(dir_)>0):
            dir_ = os.path.dirname(os.path.join(settings.MEDIA_ROOT, str(dir_)))
            if (os.path.isdir(dir_)):
                os.rmdir(os.path.join(dir_))
        self.ssRNA_id = None
        self.ssRNA_fasta = None
        self.dsDNA_fasta = None
        self.stability = None
        self.summary = None
        self.rawLogsSTDERR = None 
        self.rawLogsSTDOUT = None

    def save(self, *args, **kwargs):
        if not self.base_path:
            print("Saving")
            self.base_path = generate_random_alphanumeric(32)
            # using your function as above or anything else
            failures = 0
            while True:
                print("Trying")
                failures += 1
                try:
                    super(JobData, self).save(*args, **kwargs)
                except IntegrityError:
                    pass
                if failures > 5: # or some other arbitrary cutoff point at which things are clearly wrong
                    raise Exception()
                else:
                    self.auto_pseudoid = generate_random_alphanumeric(32)
                    break
        else:
            super(JobData, self).save(*args, **kwargs)

@receiver(models.signals.post_delete, sender=JobData)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    instance.delete_all_files()


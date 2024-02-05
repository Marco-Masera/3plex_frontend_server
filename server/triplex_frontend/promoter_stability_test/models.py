from django.db import models
from django.dispatch import receiver
from django.conf import settings
import secrets 
import os
import filecmp
from django.db import IntegrityError
from results_mng.models import LongestTranscript

ALLOWED_SPECIES = settings.ALLOWED_SPECIES
# Create your models here.
def generate_random_alphanumeric(length) -> str:
    return secrets.token_urlsafe(length).replace("/","_").replace(" ", "").replace("\t", "").replace("-", "_")

def safe_file_cmp(file_1, file_2):
    if (bool(file_1) and bool(file_2) and os.path.isfile(file_2.path) and os.path.isfile(file_1.path)):
        return filecmp.cmp(file_1.path, file_2.path)
    else:
        return file_1.path.split("/")[-1] == file_2.path.split("/")[-1]

state_choices = [
        ("Created", "Created"),
        ("Submitted","Submitted"),
        ("Ready", "Ready"),
        ("Expired", "Expired"),
        ("Cancelled","Cancelled"),
        ("Failed","Failed")
]

class StabilityTestJobData(models.Model):

    state = models.CharField(max_length=16, choices = state_choices, default = "Created")

    date = models.DateTimeField(auto_now_add=True, auto_now=False)
    triplex_params = models.JSONField()
    base_path = models.CharField(max_length=64, blank=False, unique=True)
    species = models.CharField(max_length=32, null=True, default=None, choices=ALLOWED_SPECIES)
    ssRNA_id = models.ForeignKey(LongestTranscript, on_delete=models.PROTECT, default=None, null=True)
    ssRNA_fasta = models.FileField(default=None, null=True)
    genes_all = models.FileField(default=None, null=True)
    genes_of_interest = models.FileField(default=None, null=True)

    rawLogsSTDOUT = models.FileField(default=None, null=True,blank=True)
    rawLogsSTDERR = models.FileField(default=None, null=True,blank=True)

    STABILITY_BEST = models.FileField(null=True, default=None)
    STABILITY_NORM = models.FileField(null=True, default=None)
    STABILITY_BEST_FGSEA_RES = models.FileField(null=True, default=None)
    STABILITY_BEST_LEADING_EDGE = models.FileField(null=True, default=None)
    STABILITY_BEST_ENRICHMENT_PLOT = models.FileField(null=True, default=None)
    STABILITY_BEST_STABILITY_COMP_BOXPLOT = models.FileField(null=True, default=None)
    STABILITY_BEST_STABILITY_COMP = models.FileField(null=True, default=None)
    STABILITY_NORM_FGSEA_RES = models.FileField(null=True, default=None)
    STABILITY_NORM_LEADING_EDGE = models.FileField(null=True, default=None)
    STABILITY_NORM_ENRICHMENT_PLOT = models.FileField(null=True, default=None)
    STABILITY_NORM_STABILITY_COMP_BOXPLOT = models.FileField(null=True, default=None)
    STABILITY_NORM_STABILITY_COMP = models.FileField(null=True, default=None)

    #Cleaned up keep tracks of the job history, if it was cleaned up after not being accessed for some time
    cleaned_up = models.BooleanField(default=False)

    export_tarball = models.FileField(default=None, null=True, blank=True)
    export_hash = models.CharField(max_length=128, null=True, blank=True, default=None)

    def set_export_file(self, tarball, hashed):
        self.export_tarball = tarball
        self.export_hash = hashed 
        self.save()

    def __str__(self):
        return f"{self.date} - {self.state}"

    @property
    def have_visualization(self):
        return False

    def delete_all_files(self):
        dir_ = None
        if self.export_tarball:
            if os.path.isfile(self.export_tarball.path):
                dir_ = self.export_tarball.path
                os.remove(self.export_tarball.path)
        if self.ssRNA_fasta:
            if os.path.isfile(self.ssRNA_fasta.path):
                dir_ = self.ssRNA_fasta.path
                os.remove(self.ssRNA_fasta.path)
        if self.rawLogsSTDOUT:
            if os.path.isfile(self.rawLogsSTDOUT.path):
                dir_ = self.rawLogsSTDOUT.path
                os.remove(self.rawLogsSTDOUT.path)
        if self.rawLogsSTDERR:
            if os.path.isfile(self.rawLogsSTDERR.path):
                dir_ = self.rawLogsSTDERR.path
                os.remove(self.rawLogsSTDERR.path)
        if self.genes_all:
            if os.path.isfile(self.genes_all.path):
                dir_ = self.genes_all.path
                os.remove(self.genes_all.path)
        if self.genes_of_interest:
            if os.path.isfile(self.genes_of_interest.path):
                dir_ = self.genes_of_interest.path
                os.remove(self.genes_of_interest.path)
        others = [
            'STABILITY_BEST', 'STABILITY_NORM', 'STABILITY_BEST_FGSEA_RES', 'STABILITY_BEST_LEADING_EDGE',
            'STABILITY_BEST_ENRICHMENT_PLOT', 'STABILITY_BEST_STABILITY_COMP_BOXPLOT', 'STABILITY_BEST_STABILITY_COMP',
            'STABILITY_NORM_FGSEA_RES', 'STABILITY_NORM_LEADING_EDGE', 'STABILITY_NORM_ENRICHMENT_PLOT',
            'STABILITY_NORM_STABILITY_COMP_BOXPLOT', 'STABILITY_NORM_STABILITY_COMP'
        ]
        for variable_name in others:
            file_field = getattr(self, variable_name)
            if file_field:
                if os.path.isfile(file_field.path):
                    os.remove(file_field.path)

        if (dir_ is not None and len(dir_)>0):
            dir_ = os.path.dirname(os.path.join(settings.MEDIA_ROOT, str(dir_)))
            if (os.path.isdir(dir_)):
                os.rmdir(os.path.join(dir_))
        self.ssRNA_id = None
        self.ssRNA_fasta = None
        self.rawLogsSTDERR = None 
        self.rawLogsSTDOUT = None

    def save(self, *args, **kwargs):
        if not self.base_path:
            self.base_path = "stab_test" + generate_random_alphanumeric(32)
            # using your function as above or anything else
            failures = 0
            while True:
                failures += 1
                try:
                    super(StabilityTestJobData, self).save(*args, **kwargs)
                except IntegrityError:
                    pass
                if failures > 5: # or some other arbitrary cutoff point at which things are clearly wrong
                    raise Exception()
                else:
                    self.auto_pseudoid = generate_random_alphanumeric(32)
                    break
        else:
            super(StabilityTestJobData, self).save(*args, **kwargs)


@receiver(models.signals.post_delete, sender=StabilityTestJobData)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    instance.delete_all_files()
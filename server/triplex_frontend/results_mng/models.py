from django.db import models
from django.dispatch import receiver
from django.conf import settings
import secrets 
import os
from django.db import IntegrityError


def generate_random_alphanumeric(length) -> str:
    return secrets.token_urlsafe(length).replace("/","_").replace(" ", "").replace("\t", "")


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
    hash_code = models.CharField(max_length=20)

    date = models.DateTimeField(auto_now_add=True, auto_now=False)
    triplex_params = models.JSONField()
    
    base_path = models.CharField(max_length=17, blank=False, unique=True)

    ssRNA_id = models.IntegerField(default=None, null=True)
    ssRNA_fasta = models.FileField(default=None, null=True)
    dsDNA_fasta = models.FileField(default=None, null=True)
    stability = models.FileField(default=None, null=True)
    summary = models.FileField(default=None, null=True)

    #Cleaned up keep tracks of the job history, if it was cleaned up after not being accessed for some time
    cleaned_up = models.BooleanField(default=False)

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
        if (dir_ is not None):
            dir_ = os.path.dirname(os.path.join(settings.MEDIA_ROOT, str(dir_)))
            if (os.path.isdir(dir_)):
                os.rmdir(os.path.join(dir_))
        self.ssRNA_id = None
        self.ssRNA_fasta = None
        self.dsDNA_fasta = None
        self.stability = None
        self.summary = None

    def save(self, *args, **kwargs):
        if not self.base_path:
            print("Saving")
            self.base_path = generate_random_alphanumeric(16)
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
                    self.auto_pseudoid = generate_random_alphanumeric(16)
                    break
        else:
            super(JobData, self).save(*args, **kwargs)

@receiver(models.signals.post_delete, sender=JobData)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    instance.delete_all_files()


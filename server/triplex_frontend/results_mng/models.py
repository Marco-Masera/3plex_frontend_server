from django.db import models
from token_queue_mng.models import Token
from django.dispatch import receiver
import os

class JobData(models.Model):
    token = models.ForeignKey(Token, on_delete=models.CASCADE)
    ssRna_id = models.IntegerField(default=None, null=True)
    ssRna_fasta = models.FileField(default=None, null=True)
    stability = models.FileField(default=None, null=True)
    summary = models.FileField(default=None, null=True)


@receiver(models.signals.post_delete, sender=JobData)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.ssRna_id:
        if os.path.isfile(instance.ssRna_id.path):
            os.remove(instance.ssRna_id.path)
    if instance.ssRna_fasta:
        if os.path.isfile(instance.ssRna_fasta.path):
            os.remove(instance.ssRna_fasta.path)
    if instance.stability:
        if os.path.isfile(instance.stability.path):
            os.remove(instance.stability.path)
    if instance.summary:
        if os.path.isfile(instance.summary.path):
            os.remove(instance.summary.path)
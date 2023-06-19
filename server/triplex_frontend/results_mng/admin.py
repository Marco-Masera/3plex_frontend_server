from django.contrib import admin
from .models import *


@admin.register(JobData)
class JobDataAdmin(admin.ModelAdmin):
    pass

@admin.register(LongestTranscript)
class LongestTranscriptAdmin(admin.ModelAdmin):
    pass

@admin.register(DnaTargetSites)
class DsDNATargetAdmin(admin.ModelAdmin):
    pass

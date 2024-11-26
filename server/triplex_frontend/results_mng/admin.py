from django.contrib import admin
from .models import *


@admin.register(JobData)
class JobDataAdmin(admin.ModelAdmin):
    readonly_fields = ("ssRNA_id",)
    list_filter = ('state','date','species')
    search_fields = ('state','date','species')
    ordering = ('-date',)

@admin.register(LongestTranscript)
class LongestTranscriptAdmin(admin.ModelAdmin):
    pass

@admin.register(DnaTargetSites)
class DsDNATargetAdmin(admin.ModelAdmin):
    pass

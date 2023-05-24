from django.contrib import admin
from .models import *

@admin.register(JobData)
class JobDataAdmin(admin.ModelAdmin):
    pass

from django.contrib import admin
from .models import *

# Register your models here.
@admin.register(StabilityTestJobData)
class StabilityTestJobDataAdmin(admin.ModelAdmin):
    readonly_fields = ("ssRNA_id",)

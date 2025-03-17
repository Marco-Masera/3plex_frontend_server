from django.contrib import admin
from .models import *


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_filter = ('submission_date',)
    search_fields = ('email_address','job_name','token','submission_date',)
    ordering = ('-submission_date',)

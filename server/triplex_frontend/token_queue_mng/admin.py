from django.contrib import admin
from .models import *


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    pass

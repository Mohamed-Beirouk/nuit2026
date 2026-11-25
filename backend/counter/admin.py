from django.contrib import admin

from .models import Claim, Counter

admin.site.register(Counter)
admin.site.register(Claim)

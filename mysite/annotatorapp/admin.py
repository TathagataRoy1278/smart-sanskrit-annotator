from django.contrib import admin
from .models import Sentences,linetypes,WordOptions,Wordsinsentence


admin.site.register(Sentences)
admin.site.register(Wordsinsentence)
admin.site.register(Wordoptions)
admin.site.register(linetypes)
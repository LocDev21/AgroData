from django.contrib import admin
from .models import *
#----------------------------ENREGISTREMENT DES MODELS---------------------------------
admin.site.register(Client)
admin.site.register(Vente)
admin.site.register(Facture)
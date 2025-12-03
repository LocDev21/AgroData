from django.contrib import admin
from .models import Producteur, Parcelle, Recolte

#----------------------------ENREGISTREMENT DES MODELS---------------------------------
admin.site.register(Producteur)
admin.site.register(Parcelle)
admin.site.register(Recolte)
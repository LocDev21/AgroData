from django.db import models
from producteurs.models import Recolte

#----------------------------Table Transformation---------------------------
ETAPES_CHOICES = [
    ('LYOPHILISATION','Lyophilisation'),
    ('CONDITIONNEMENT','Conditionnement'),
    ('STOCKE','Stocké'),
]
class Transformation(models.Model):
    code_lot = models.CharField(max_length=50)
    recolte = models.ForeignKey(Recolte,on_delete=models.CASCADE)
    etape = models.CharField(max_length=20, choices=ETAPES_CHOICES)
    quantite_depart = models.FloatField()
    quantite_finale = models.FloatField()
    date_debut = models.DateField()
    date_fin = models.DateField()

    def __str__(self):          
        return f"LOT {self.code_lot}"

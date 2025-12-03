from django.db import models

#----------------------------Table Producteur---------------------------
class Producteur(models.Model):
    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=100)
    adresse = models.CharField(max_length=50)
    telephone = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return f"{self.nom} {self.prenom} {self.telephone}"

#----------------------------Table Parcelle---------------------------
class Parcelle(models.Model):
    nom = models.CharField(max_length=50)
    superficie = models.FloatField()
    adresse = models.CharField(max_length =50)
    producteur = models.ForeignKey(Producteur, on_delete= models.CASCADE)

    def __str__(self):
        return f"{self.nom} {self.superficie} {self.adresse}"

#----------------------------Table Recolte---------------------------
class Recolte (models.Model):
    fruit = models.CharField(max_length=50)
    quantite = models.FloatField()
    date_recolte = models.DateField()
    producteur = models.ForeignKey(Producteur, on_delete=models.CASCADE)
    parcelle = models.ForeignKey(Parcelle, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.fruit} {self.quantite}"



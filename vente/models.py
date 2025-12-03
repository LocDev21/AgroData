from django.db import models
from stock.models import Stock
#----------------------------Table Client---------------------------
class Client (models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=15, unique=True)
    adresse = models.CharField(max_length=50)
    email = models.EmailField(max_length=254, unique=True)

    def __str__(self):
        return f"{self.nom} {self.prenom} {self.telephone}"
    
#----------------------------Table Vente---------------------------
class Vente (models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantite_vendue = models.FloatField()
    prix_unitaire = models.DecimalField(max_digits=10,decimal_places=2)
    date_vente = models.DateField()
    montant_total = models.DecimalField(max_digits=10,decimal_places=2)

    def __str__(self):
        return f"QTE {self.quantite_vendue} PU : {self.prix_unitaire} MTotal : {self.montant_total}"
    
#----------------------------Table Facture---------------------------
PAIEMENT_CHOICES = [
    ('LIQUIDE','Liquide'),
    ('OM','Orange Money'),
    ('MOMO','Mobile Money'),
    ('PAYCARD','Paycard')
]
STATUT_CHOICES = [
    ('PAYER','Payer'),
    ('ATTENTE','En Attente')
]
class Facture (models.Model):
    vente = models.ForeignKey(Vente, on_delete=models.CASCADE)
    numero_facture = models.IntegerField()
    date_emission = models.DateField(auto_created=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    mode_paiement = models.CharField(max_length=20, choices=PAIEMENT_CHOICES)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES)
    
    def __str__(self):
        return f"Facture No: {self.numero_facture} Montant: {self.montant} Statut: {self.statut}"


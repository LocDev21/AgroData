from django.db import models
from transformation.models import Transformation

#----------------------------Table Stock---------------------------
UNITE_CHOICES = [
    ('KG','Kg'),
    ('TONNE','Tonne'),
    ('SACHET','Sachet'),
    ('BOITE','Boite')
]
class Stock (models.Model):
    lot = models.ForeignKey(Transformation, on_delete=models.CASCADE)
    produit = models.CharField(max_length=100)
    quantite_disponible = models.FloatField()
    unite_mesure = models.CharField(max_length=10, choices = UNITE_CHOICES)
    date_mise_a_jour = models.DateField()

    def __str__(self):
        return f"{self.produit} disponible: {self.quantite_disponible}  {self.unite_mesure}" 


class StockMovement(models.Model):
    """Historique des mouvements de stock liés aux ventes et ajustements."""
    REASON_CHOICES = [
        ('VENTE', 'Vente'),
        ('RESTORE', 'Restauration'),
        ('AJUST', 'Ajustement'),
        ('MODIF', 'Modification'),
    ]

    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='movements')
    vente = models.ForeignKey('vente.Vente', null=True, blank=True, on_delete=models.SET_NULL)
    change = models.FloatField(help_text='Quantité modifiée (négatif pour sortie, positif pour entrée)')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, default='VENTE')
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_reason_display()} {self.change} on {self.stock.produit} ({self.created_at})"
    

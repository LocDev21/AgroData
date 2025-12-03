from django.urls import path
from . import views

urlpatterns = [
    #----------------------- Routes Producteur -----------------------------------------
    path('producteurs/', views.liste_producteurs, name='liste_producteurs'),
    path('producteurs/ajouter/', views.ajouter_producteur, name='ajouter_producteur'),
    path('producteurs/<int:id>/', views.details_producteur, name='details_producteur'),
    path('producteurs/<int:id>/modifier/', views.modifier_producteur, name='modifier_producteur'),
    path('producteurs/<int:id>/supprimer/', views.supprimer_producteur, name='supprimer_producteur'),

    #----------------------- Routes Parcelle -----------------------------------------
    path('parcelles/', views.liste_parcelles, name='liste_parcelles'),
    path('parcelles/ajouter/', views.ajouter_parcelle, name='ajouter_parcelle'),
    path('parcelles/<int:id>/', views.details_parcelle, name='details_parcelle'),
    path('parcelles/<int:id>/modifier/', views.modifier_parcelle, name='modifier_parcelle'),
    path('parcelles/<int:id>/supprimer/', views.supprimer_parcelle, name='supprimer_parcelle'),

    #----------------------- Routes Récolte -----------------------------------------
    path('recoltes/', views.liste_recoltes, name='liste_recoltes'),
    path('recoltes/ajouter/', views.ajouter_recolte, name='ajouter_recolte'),
    path('recoltes/<int:id>/', views.details_recolte, name='details_recolte'),
    path('recoltes/<int:id>/modifier/', views.modifier_recolte, name='modifier_recolte'),
    path('recoltes/<int:id>/supprimer/', views.supprimer_recolte, name='supprimer_recolte'),
]

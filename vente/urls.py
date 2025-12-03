from django.urls import path
from . import views

urlpatterns = [
    # ------------------ Routes Clients ------------------
    path('clients/', views.liste_clients, name='liste_clients'),
    path('clients/ajouter/', views.ajouter_client, name='ajouter_client'),
    path('clients/<int:id>/', views.details_client, name='details_client'),
    path('clients/<int:id>/modifier/', views.modifier_client, name='modifier_client'),
    path('clients/<int:id>/supprimer/', views.supprimer_client, name='supprimer_client'),

    # ------------------ Routes Ventes ------------------
    path('ventes/', views.liste_ventes, name='liste_ventes'),
    path('ventes/ajouter/', views.ajouter_vente, name='ajouter_vente'),
    path('ventes/overview/', views.overview, name='vente_overview'),
    path('ventes/<int:id>/', views.details_vente, name='details_vente'),
    path('ventes/<int:id>/modifier/', views.modifier_vente, name='modifier_vente'),
    path('ventes/<int:id>/supprimer/', views.supprimer_vente, name='supprimer_vente'),

    # ------------------ Routes Factures ------------------
    path('factures/', views.liste_factures, name='liste_factures'),
    path('factures/ajouter/', views.ajouter_facture, name='ajouter_facture'),
    path('factures/<int:id>/', views.details_facture, name='details_facture'),
    path('factures/<int:id>/print/', views.print_facture, name='print_facture'),
    path('factures/<int:id>/download/', views.download_facture, name='download_facture'),
    path('factures/<int:id>/modifier/', views.modifier_facture, name='modifier_facture'),
    path('factures/<int:id>/supprimer/', views.supprimer_facture, name='supprimer_facture'),
]

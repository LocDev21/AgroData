from django.urls import path
from . import views

urlpatterns = [
    path('stocks/', views.liste_stocks, name='liste_stocks'),
    path('stocks/ajouter/', views.ajouter_stock, name='ajouter_stock'),
    path('stocks/<int:id>/', views.details_stock, name='details_stock'),
    path('stocks/<int:id>/modifier/', views.modifier_stock, name='modifier_stock'),
    path('stocks/<int:id>/supprimer/', views.supprimer_stock, name='supprimer_stock'),
]

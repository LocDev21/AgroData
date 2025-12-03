from django.urls import path
from . import views

urlpatterns = [
    path('transformations/', views.liste_transformations, name='liste_transformations'),
    path('transformations/ajouter/', views.ajouter_transformation, name='ajouter_transformation'),
    path('transformations/<int:id>/', views.details_transformation, name='details_transformation'),
    path('transformations/<int:id>/modifier/', views.modifier_transformation, name='modifier_transformation'),
    path('transformations/<int:id>/supprimer/', views.supprimer_transformation, name='supprimer_transformation'),
]

from django.shortcuts import render, redirect, get_object_or_404
from producteurs.models import Recolte
from .models import Transformation

#---------------------------------- VUES POUR LES TRANSFORMATIONS ---------------------------------

def liste_transformations(request):
    transformations = Transformation.objects.all()
    return render(request, 'transformation/liste.html', {'transformations': transformations})


def ajouter_transformation(request):
    recoltes = Recolte.objects.all()
    if request.method == "POST":
        code_lot = request.POST['code_lot']
        recolte_id = request.POST['recolte']
        recolte = get_object_or_404(Recolte, id=recolte_id)
        etape = request.POST['etape']
        quantite_depart = request.POST['quantite_depart']
        quantite_finale = request.POST['quantite_finale']
        date_debut = request.POST['date_debut']
        date_fin = request.POST['date_fin']

        Transformation.objects.create(
            code_lot=code_lot,
            recolte=recolte,
            etape=etape,
            quantite_depart=quantite_depart,
            quantite_finale=quantite_finale,
            date_debut=date_debut,
            date_fin=date_fin
        )
        return redirect('liste_transformations')
    return render(request, 'transformation/ajouter.html', {'recoltes': recoltes})


def modifier_transformation(request, id):
    transformation = get_object_or_404(Transformation, id=id)
    recoltes = Recolte.objects.all()

    if request.method == "POST":
        transformation.code_lot = request.POST['code_lot']
        transformation.recolte = get_object_or_404(Recolte, id=request.POST['recolte'])
        transformation.etape = request.POST['etape']
        transformation.quantite_depart = request.POST['quantite_depart']
        transformation.quantite_finale = request.POST['quantite_finale']
        transformation.date_debut = request.POST['date_debut']
        transformation.date_fin = request.POST['date_fin']

        transformation.save()
        return redirect('liste_transformations')

    return render(request, 'transformation/modifier.html', {
        'transformation': transformation,
        'recoltes': recoltes
    })


def supprimer_transformation(request, id):
    transformation = get_object_or_404(Transformation, id=id)
    transformation.delete()
    return redirect('liste_transformations')


def details_transformation(request, id):
    transformation = get_object_or_404(Transformation, id=id)
    return render(request, 'transformation/details.html', {'transformation': transformation})

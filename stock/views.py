from django.shortcuts import render, get_object_or_404, redirect
from .models import Stock
from transformation.models import Transformation

#---------------------------------- VUES POUR LES STOCKS ---------------------------------

def liste_stocks(request):
    stocks = Stock.objects.all()
    return render(request, 'stock/liste.html', {'stocks': stocks})


def ajouter_stock(request):
    transformations = Transformation.objects.all()
    if request.method == "POST":
        lot_id = request.POST['lot']
        lot = get_object_or_404(Transformation, id=lot_id)
        produit = request.POST['produit']
        quantite_disponible = request.POST['quantite_disponible']
        unite_mesure = request.POST['unite_mesure']
        date_mise_a_jour = request.POST['date_mise_a_jour']

        Stock.objects.create(
            lot=lot,
            produit=produit,
            quantite_disponible=quantite_disponible,
            unite_mesure=unite_mesure,
            date_mise_a_jour=date_mise_a_jour
        )
        return redirect('liste_stocks')
    return render(request, 'stock/ajouter.html', {'transformations': transformations})


def modifier_stock(request, id):
    stock = get_object_or_404(Stock, id=id)
    transformations = Transformation.objects.all()

    if request.method == "POST":
        stock.lot = get_object_or_404(Transformation, id=request.POST['lot'])
        stock.produit = request.POST['produit']
        stock.quantite_disponible = request.POST['quantite_disponible']
        stock.unite_mesure = request.POST['unite_mesure']
        stock.date_mise_a_jour = request.POST['date_mise_a_jour']

        stock.save()
        return redirect('liste_stocks')

    return render(request, 'stock/modifier.html', {'stock': stock, 'transformations': transformations})


def supprimer_stock(request, id):
    stock = get_object_or_404(Stock, id=id)
    stock.delete()
    return redirect('liste_stocks')


def details_stock(request, id):
    stock = get_object_or_404(Stock, id=id)
    return render(request, 'stock/details.html', {'stock': stock})

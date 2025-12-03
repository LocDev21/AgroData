from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Producteur, Parcelle, Recolte

#---------------------------------- VUES POUR LES PRODUCTEURS ---------------------------------

from django.core.paginator import Paginator
from django.db.models import Q, Count


def liste_producteurs(request):
    """List producteurs with optional search and filters.

    Supported GET params:
    - q: search across nom, prenom, telephone
    - has_parcelle: '1' to require at least one parcelle, '0' to require none
    - has_recolte: '1' to require at least one recolte, '0' to require none
    - page: page number for pagination
    """
    qs = Producteur.objects.all()

    # annotate counts to allow filtering without extra queries later
    qs = qs.annotate(_parcelle_count=Count('parcelle'), _recolte_count=Count('recolte'))

    # search q can be applied to a specific field when 'field' param is present
    q = request.GET.get('q', '').strip()
    field = request.GET.get('field', '').strip()
    allowed_fields = {'nom', 'prenom', 'adresse', 'telephone'}
    if q:
        if field in allowed_fields:
            qs = qs.filter(**{f"{field}__icontains": q})
        else:
            qs = qs.filter(
                Q(nom__icontains=q) | Q(prenom__icontains=q) | Q(telephone__icontains=q)
            )

    has_parcelle = request.GET.get('has_parcelle')
    if has_parcelle == '1':
        qs = qs.filter(_parcelle_count__gt=0)
    elif has_parcelle == '0':
        qs = qs.filter(_parcelle_count=0)

    has_recolte = request.GET.get('has_recolte')
    if has_recolte == '1':
        qs = qs.filter(_recolte_count__gt=0)
    elif has_recolte == '0':
        qs = qs.filter(_recolte_count=0)

    # filter by fruits (multi-select)
    selected_fruits = request.GET.getlist('fruits')
    if selected_fruits:
        qs = qs.filter(recolte__fruit__in=selected_fruits).distinct()

    # prefetch related small sets to avoid N+1 when rendering parcelles/recoltes
    qs = qs.prefetch_related('parcelle_set', 'recolte_set')

    # pagination
    page_size = 12
    paginator = Paginator(qs.order_by('nom', 'prenom'), page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'producteurs': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'query': q,
        'has_parcelle': has_parcelle,
        'has_recolte': has_recolte,
        'field': field,
        'selected_fruits': selected_fruits,
        # supply available fruits to populate the multi-select
        'fruits_choices': list(Recolte.objects.order_by('fruit').values_list('fruit', flat=True).distinct()),
    }
    return render(request, 'producteur/liste.html', context)


def ajouter_producteur(request):
    parcelles = Parcelle.objects.all()
    if request.method == "POST":
        # if producteur already created via AJAX, reuse it
        existing_id = request.POST.get('producteur_id') or request.POST.get('producteur')
        if existing_id:
            try:
                producteur = Producteur.objects.get(id=int(existing_id))
            except Exception:
                producteur = None
        else:
            producteur = None

        if not producteur:
            # create the producteur
            nom = request.POST.get('nom', '').strip()
            prenom = request.POST.get('prenom', '').strip()
            adresse = request.POST.get('adresse', '').strip()
            telephone = request.POST.get('telephone', '').strip()

            producteur = Producteur.objects.create(
                nom=nom,
                prenom=prenom,
                adresse=adresse,
                telephone=telephone
            )

        # If this is an AJAX call asking to create only the producteur (from ajouter page), return JSON
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1':
            return JsonResponse({'id': producteur.id, 'nom': f"{producteur.nom} {producteur.prenom}"})

        # Create any new parcelles submitted (arrays)
        parcelle_noms = request.POST.getlist('parcelle_nom')
        parcelle_superficies = request.POST.getlist('parcelle_superficie')
        parcelle_adresses = request.POST.getlist('parcelle_adresse')

        new_parcelles = []
        for i, pnom in enumerate(parcelle_noms):
            pnom = pnom.strip()
            if not pnom:
                continue
            superficie = parcelle_superficies[i] if i < len(parcelle_superficies) else ''
            adresse_p = parcelle_adresses[i] if i < len(parcelle_adresses) else ''
            parc = Parcelle.objects.create(
                nom=pnom,
                superficie=(superficie or 0),
                adresse=adresse_p,
                producteur=producteur
            )
            new_parcelles.append(parc)

        # Create recoltes (can reference existing parcelles by id or new-parcelle indexes 'new-0')
        recolte_fruits = request.POST.getlist('recolte_fruit')
        recolte_quantites = request.POST.getlist('recolte_quantite')
        recolte_dates = request.POST.getlist('recolte_date')
        recolte_parcelles = request.POST.getlist('recolte_parcelle')

        for i, fruit in enumerate(recolte_fruits):
            fruit = fruit.strip()
            if not fruit:
                continue
            quantite = recolte_quantites[i] if i < len(recolte_quantites) else 0
            date_recolte = recolte_dates[i] if i < len(recolte_dates) else None
            parcelle_ref = recolte_parcelles[i] if i < len(recolte_parcelles) else ''

            # determine the Parcelle instance
            parcelle_obj = None
            if parcelle_ref.startswith('new-'):
                try:
                    idx = int(parcelle_ref.split('-', 1)[1])
                    parcelle_obj = new_parcelles[idx]
                except Exception:
                    parcelle_obj = None
            else:
                try:
                    parcelle_obj = get_object_or_404(Parcelle, id=int(parcelle_ref))
                except Exception:
                    parcelle_obj = None

            # create recolte if parcelle resolved or allow null parcelle
            Recolte.objects.create(
                fruit=fruit,
                quantite=(quantite or 0),
                date_recolte=(date_recolte or None),
                producteur=producteur,
                parcelle=parcelle_obj
            )

        return redirect('details_producteur', producteur.id)

    return render(request, 'producteur/ajouter.html', {'parcelles': parcelles})


def modifier_producteur(request, id):
    producteur = get_object_or_404(Producteur, id=id)
    # fetch related objects for the form
    parcelles_existantes = list(producteur.parcelle_set.all())
    recoltes_existantes = list(producteur.recolte_set.all())

    if request.method == "POST":
        # Update basic producteur info
        producteur.nom = request.POST.get('nom', producteur.nom).strip()
        producteur.prenom = request.POST.get('prenom', producteur.prenom).strip()
        producteur.adresse = request.POST.get('adresse', producteur.adresse).strip()
        producteur.telephone = request.POST.get('telephone', producteur.telephone).strip()
        producteur.save()

        # --- Parcelles ---
        parcelle_ids = request.POST.getlist('parcelle_id')
        parcelle_noms = request.POST.getlist('parcelle_nom')
        parcelle_superficies = request.POST.getlist('parcelle_superficie')
        parcelle_adresses = request.POST.getlist('parcelle_adresse')
        parcelle_deletes = request.POST.getlist('parcelle_delete')  # list of ids to delete

        new_parcelles = []
        for i, nom in enumerate(parcelle_noms):
            nom = nom.strip()
            pid = parcelle_ids[i] if i < len(parcelle_ids) else ''
            superficie = parcelle_superficies[i] if i < len(parcelle_superficies) else 0
            adresse_p = parcelle_adresses[i] if i < len(parcelle_adresses) else ''

            if pid:  # existing parcelle
                try:
                    parc = Parcelle.objects.get(id=int(pid), producteur=producteur)
                except Exception:
                    continue
                if str(parc.id) in parcelle_deletes:
                    parc.delete()
                    continue
                parc.nom = nom or parc.nom
                try:
                    parc.superficie = float(superficie) if superficie != '' else parc.superficie
                except Exception:
                    pass
                parc.adresse = adresse_p or parc.adresse
                parc.save()
            else:
                # new parcelle
                if not nom:
                    continue
                try:
                    superficie_val = float(superficie) if superficie != '' else 0
                except Exception:
                    superficie_val = 0
                parc = Parcelle.objects.create(
                    nom=nom,
                    superficie=superficie_val,
                    adresse=adresse_p,
                    producteur=producteur
                )
                new_parcelles.append(parc)

        # --- Récoltes ---
        recolte_ids = request.POST.getlist('recolte_id')
        recolte_fruits = request.POST.getlist('recolte_fruit')
        recolte_quantites = request.POST.getlist('recolte_quantite')
        recolte_dates = request.POST.getlist('recolte_date')
        recolte_parcelles = request.POST.getlist('recolte_parcelle')
        recolte_deletes = request.POST.getlist('recolte_delete')

        for i, fruit in enumerate(recolte_fruits):
            fruit = fruit.strip()
            rid = recolte_ids[i] if i < len(recolte_ids) else ''
            quantite = recolte_quantites[i] if i < len(recolte_quantites) else 0
            date_r = recolte_dates[i] if i < len(recolte_dates) else None
            parc_ref = recolte_parcelles[i] if i < len(recolte_parcelles) else ''

            # Resolve parcelle: existing id or newly created referenced by new-<index>
            parcelle_obj = None
            if parc_ref:
                if isinstance(parc_ref, str) and parc_ref.startswith('new-'):
                    try:
                        idx = int(parc_ref.split('-', 1)[1])
                        parcelle_obj = new_parcelles[idx]
                    except Exception:
                        parcelle_obj = None
                else:
                    try:
                        parcelle_obj = Parcelle.objects.get(id=int(parc_ref))
                    except Exception:
                        parcelle_obj = None

            if rid:  # existing recolte
                try:
                    recolte = Recolte.objects.get(id=int(rid), producteur=producteur)
                except Exception:
                    continue
                if str(recolte.id) in recolte_deletes:
                    recolte.delete()
                    continue
                recolte.fruit = fruit or recolte.fruit
                try:
                    recolte.quantite = float(quantite) if quantite != '' else recolte.quantite
                except Exception:
                    pass
                recolte.date_recolte = date_r or recolte.date_recolte
                recolte.parcelle = parcelle_obj or recolte.parcelle
                recolte.save()
            else:
                # new recolte
                if not fruit:
                    continue
                try:
                    quant_val = float(quantite) if quantite != '' else 0
                except Exception:
                    quant_val = 0
                Recolte.objects.create(
                    fruit=fruit,
                    quantite=quant_val,
                    date_recolte=(date_r or None),
                    producteur=producteur,
                    parcelle=parcelle_obj
                )

        return redirect('details_producteur', producteur.id)

    # GET: render form with existing parcelles and recoltes
    parcelles = Parcelle.objects.filter(producteur=producteur)
    recoltes = Recolte.objects.filter(producteur=producteur)
    return render(request, 'producteur/modifier.html', {'producteur': producteur, 'parcelles': parcelles, 'recoltes': recoltes})


def supprimer_producteur(request, id):
    producteur = get_object_or_404(Producteur, id=id)
    producteur.delete()
    return redirect('liste_producteurs')


def details_producteur(request, id):
    producteur = get_object_or_404(Producteur, id=id)
    return render(request, 'producteur/details.html', {'producteur': producteur})


#---------------------------------- VUES POUR LES PARCELLES ---------------------------------

def liste_parcelles(request):
    parcelles = Parcelle.objects.all()
    return render(request, 'parcelle/liste.html', {'parcelles': parcelles})


def ajouter_parcelle(request):
    producteurs = Producteur.objects.all()
    if request.method == "POST":
        nom = request.POST['nom']
        superficie = request.POST['superficie']
        adresse = request.POST['adresse']
        producteur_id = request.POST['producteur']
        producteur = get_object_or_404(Producteur, id=producteur_id)

        Parcelle.objects.create(
            nom=nom,
            superficie=superficie,
            adresse=adresse,
            producteur=producteur
        )
        # if AJAX request, return JSON with created parcelle id and name
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1':
            parc = Parcelle.objects.filter(producteur=producteur, nom=nom).order_by('-id').first()
            if parc:
                return JsonResponse({'id': parc.id, 'nom': parc.nom})
            return JsonResponse({'error': 'Création failed'}, status=400)
        return redirect('liste_parcelles')
    return render(request, 'parcelle/ajouter.html', {'producteurs': producteurs})


def modifier_parcelle(request, id):
    parcelle = get_object_or_404(Parcelle, id=id)
    producteurs = Producteur.objects.all()

    if request.method == "POST":
        parcelle.nom = request.POST['nom']
        parcelle.superficie = request.POST['superficie']
        parcelle.adresse = request.POST['adresse']
        producteur_id = request.POST['producteur']
        parcelle.producteur = get_object_or_404(Producteur, id=producteur_id)

        parcelle.save()
        return redirect('liste_parcelles')

    return render(request, 'parcelle/modifier.html', {'parcelle': parcelle, 'producteurs': producteurs})


def supprimer_parcelle(request, id):
    parcelle = get_object_or_404(Parcelle, id=id)
    parcelle.delete()
    return redirect('liste_parcelles')


def details_parcelle(request, id):
    parcelle = get_object_or_404(Parcelle, id=id)
    return render(request, 'parcelle/details.html', {'parcelle': parcelle})


#---------------------------------- VUES POUR LES RECOLTES ---------------------------------

def liste_recoltes(request):
    recoltes = Recolte.objects.all()
    return render(request, 'recolte/liste.html', {'recoltes': recoltes})


def ajouter_recolte(request):
    producteurs = Producteur.objects.all()
    parcelles = Parcelle.objects.all()

    if request.method == "POST":
        fruit = request.POST['fruit']
        quantite = request.POST['quantite']
        date_recolte = request.POST['date_recolte']
        producteur = get_object_or_404(Producteur, id=request.POST['producteur'])
        parcelle_id = request.POST.get('parcelle')
        parcelle = None
        if parcelle_id:
            try:
                parcelle = get_object_or_404(Parcelle, id=parcelle_id)
            except Exception:
                parcelle = None

        recolte = Recolte.objects.create(
            fruit=fruit,
            quantite=quantite,
            date_recolte=date_recolte,
            producteur=producteur,
            parcelle=parcelle
        )
        # if AJAX, return JSON
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1':
            return JsonResponse({'id': recolte.id, 'fruit': recolte.fruit, 'parcelle_id': parcelle.id if parcelle else None})
        return redirect('liste_recoltes')

    return render(request, 'recolte/ajouter.html', {'producteurs': producteurs, 'parcelles': parcelles})


def modifier_recolte(request, id):
    recolte = get_object_or_404(Recolte, id=id)
    producteurs = Producteur.objects.all()
    parcelles = Parcelle.objects.all()

    if request.method == "POST":
        recolte.fruit = request.POST['fruit']
        recolte.quantite = request.POST['quantite']
        recolte.date_recolte = request.POST['date_recolte']
        recolte.producteur = get_object_or_404(Producteur, id=request.POST['producteur'])
        recolte.parcelle = get_object_or_404(Parcelle, id=request.POST['parcelle'])

        recolte.save()
        return redirect('liste_recoltes')

    return render(request, 'recolte/modifier.html', {'recolte': recolte, 'producteurs': producteurs, 'parcelles': parcelles})


def supprimer_recolte(request, id):
    recolte = get_object_or_404(Recolte, id=id)
    recolte.delete()
    return redirect('liste_recoltes')


def details_recolte(request, id):
    recolte = get_object_or_404(Recolte, id=id)
    return render(request, 'recolte/details.html', {'recolte': recolte})

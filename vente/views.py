from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Client, Vente, Facture
from stock.models import Stock, StockMovement
from datetime import date
from django.core.paginator import Paginator
from django.contrib import messages
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.db.models import Q

#---------------------------------- VUES POUR LES CLIENTS ---------------------------------

def liste_clients(request):
    clients = Client.objects.all()
    return render(request, 'client/liste.html', {'clients': clients})


def ajouter_client(request):
    if request.method == "POST":
        nom = request.POST.get('nom', '').strip()
        prenom = request.POST.get('prenom', '').strip()
        telephone = request.POST.get('telephone', '').strip()
        adresse = request.POST.get('adresse', '').strip()
        email = request.POST.get('email', '').strip()

        client = Client.objects.create(
            nom=nom,
            prenom=prenom,
            telephone=telephone,
            adresse=adresse,
            email=email
        )
        # AJAX support: return JSON with new client id and display name
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1':
            return JsonResponse({'id': client.id, 'name': f"{client.nom} {client.prenom}"})
        return redirect('liste_clients')
    return render(request, 'client/ajouter.html')


def modifier_client(request, id):
    client = get_object_or_404(Client, id=id)
    if request.method == "POST":
        client.nom = request.POST['nom']
        client.prenom = request.POST['prenom']
        client.telephone = request.POST['telephone']
        client.adresse = request.POST['adresse']
        client.email = request.POST['email']
        client.save()
        return redirect('liste_clients')
    return render(request, 'client/modifier.html', {'client': client})


def supprimer_client(request, id):
    client = get_object_or_404(Client, id=id)
    client.delete()
    return redirect('liste_clients')


def details_client(request, id):
    client = get_object_or_404(Client, id=id)
    return render(request, 'client/details.html', {'client': client})


#---------------------------------- VUES POUR LES VENTES ---------------------------------

def liste_ventes(request):
    # filter params
    field = request.GET.get('field', '')
    q = (request.GET.get('q') or '').strip()
    selected_product = request.GET.get('product', '')
    has_facture = request.GET.get('has_facture', '')
    min_q = request.GET.get('min_q', '')
    max_q = request.GET.get('max_q', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')

    ventes_qs = Vente.objects.select_related('client', 'stock').all()

    if field in ('', 'client') and q:
        # search by client name / prenom / telephone
        ventes_qs = ventes_qs.filter(
            Q(client__nom__icontains=q) |
            Q(client__prenom__icontains=q) |
            Q(client__telephone__icontains=q)
        )

    if field == 'facture' and q:
        # search by facture number (reverse relation)
        ventes_qs = ventes_qs.filter(facture__numero_facture__icontains=q)

    if field == 'produit' and q:
        ventes_qs = ventes_qs.filter(stock__produit__icontains=q)

    if selected_product:
        try:
            pid = int(selected_product)
            ventes_qs = ventes_qs.filter(stock__id=pid)
        except Exception:
            pass

    if has_facture == '1':
        ventes_qs = ventes_qs.filter(facture__isnull=False)
    elif has_facture == '0':
        ventes_qs = ventes_qs.filter(facture__isnull=True)

    # quantity range
    try:
        if min_q != '':
            ventes_qs = ventes_qs.filter(quantite_vendue__gte=float(min_q))
    except Exception:
        pass
    try:
        if max_q != '':
            ventes_qs = ventes_qs.filter(quantite_vendue__lte=float(max_q))
    except Exception:
        pass

    # price range
    try:
        if min_price != '':
            ventes_qs = ventes_qs.filter(prix_unitaire__gte=float(min_price))
    except Exception:
        pass
    try:
        if max_price != '':
            ventes_qs = ventes_qs.filter(prix_unitaire__lte=float(max_price))
    except Exception:
        pass

    # Avoid duplicates because of reverse joins
    ventes = ventes_qs.distinct()

    # provide products list for the template
    products = Stock.objects.order_by('produit').all()

    context = {
        'ventes': ventes,
        'field': field,
        'query': q,
        'products': products,
        'selected_product': selected_product,
        'has_facture': has_facture,
        'min_q': min_q,
        'max_q': max_q,
        'min_price': min_price,
        'max_price': max_price,
    }
    return render(request, 'vente/liste.html', context)


def ajouter_vente(request):
    clients = Client.objects.all()
    stocks = Stock.objects.all()
    if request.method == "POST":
        # Allow creating/selecting client in the same form
        client = None
        client_id = request.POST.get('client') or request.POST.get('new_client_id')
        if client_id:
            try:
                client = get_object_or_404(Client, id=int(client_id))
            except Exception:
                client = None

        if not client:
            # try to create client from new_* fields if provided
            new_nom = request.POST.get('new_nom', '').strip()
            new_prenom = request.POST.get('new_prenom', '').strip()
            new_telephone = request.POST.get('new_telephone', '').strip()
            new_email = request.POST.get('new_email', '').strip()
            new_adresse = request.POST.get('new_adresse', '').strip()
            if new_nom and new_prenom:
                # prefer to get_or_create by telephone or email to avoid duplicates
                try:
                    if new_telephone:
                        client, created = Client.objects.get_or_create(telephone=new_telephone,
                            defaults={'nom': new_nom, 'prenom': new_prenom, 'adresse': new_adresse, 'email': new_email})
                    elif new_email:
                        client, created = Client.objects.get_or_create(email=new_email,
                            defaults={'nom': new_nom, 'prenom': new_prenom, 'adresse': new_adresse, 'telephone': new_telephone})
                    else:
                        client = Client.objects.create(nom=new_nom, prenom=new_prenom, telephone=new_telephone, adresse=new_adresse, email=new_email)
                except Exception:
                    # fallback: try to create directly (may raise IntegrityError upstream)
                    try:
                        client = Client.objects.create(nom=new_nom, prenom=new_prenom, telephone=new_telephone, adresse=new_adresse, email=new_email)
                    except Exception:
                        client = None
            else:
                # no client info provided; raise error by redirecting back or leave client None
                client = None
        # if still no client, abort
        if not client:
            # simplest feedback: redirect back to form (could be improved to show message)
            return redirect('ajouter_vente')
        stock = get_object_or_404(Stock, id=request.POST['stock'])
        quantite_vendue = float(request.POST.get('quantite_vendue') or 0)
        prix_unitaire = float(request.POST.get('prix_unitaire') or 0)
        date_vente = request.POST.get('date_vente')
        montant_total = quantite_vendue * prix_unitaire

        # Strict stock option (if checked, refuse creation when insufficient stock)
        strict_stock = request.POST.get('strict_stock') == '1'
        if strict_stock and quantite_vendue > (stock.quantite_disponible or 0):
            messages.error(request, f"Stock insuffisant pour '{stock.produit}' (disponible: {stock.quantite_disponible}). Vente annulée.")
            return redirect('ajouter_vente')

        vente = Vente.objects.create(
            client=client,
            stock=stock,
            quantite_vendue=quantite_vendue,
            prix_unitaire=prix_unitaire,
            date_vente=date_vente,
            montant_total=montant_total
        )

        # Reduce stock quantity by the sold amount (or set to zero when not strict)
        try:
            original = stock.quantite_disponible or 0
            if quantite_vendue > original:
                # if strict_stock, we already returned above; otherwise set to zero and record partial
                deducted = original
                stock.quantite_disponible = 0
                messages.warning(request, f"Vente créée — stock insuffisant pour '{stock.produit}'. Quantité vendue limitée à {deducted} (stock mis à zéro).")
            else:
                deducted = quantite_vendue
                stock.quantite_disponible = original - deducted
            stock.save()
            # record movement (negative change)
            try:
                StockMovement.objects.create(stock=stock, vente=vente, change=-deducted, reason='VENTE', note=f'Vente #{vente.id}')
            except Exception:
                # ignore movement creation errors but keep processing
                pass
        except Exception:
            messages.warning(request, "Impossible de mettre à jour le stock automatiquement.")

        # Optionally create facture immediately if requested
        if request.POST.get('create_facture') == '1':
            numero_facture = request.POST.get('numero_facture') or ''
            mode_paiement = request.POST.get('mode_paiement') or 'LIQUIDE'
            statut = request.POST.get('statut') or 'ATTENTE'
            # Invoice montant is strictly the vente montant_total
            montant = float(montant_total)
            Facture.objects.create(
                vente=vente,
                numero_facture=numero_facture,
                date_emission=request.POST.get('date_emission') or date.today(),
                montant=montant,
                mode_paiement=mode_paiement,
                statut=statut
            )

        # If AJAX, return JSON with vente id and montant
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1':
            return JsonResponse({'id': vente.id, 'montant_total': float(vente.montant_total)})

        return redirect('liste_ventes')

    return render(request, 'vente/ajouter.html', {'clients': clients, 'stocks': stocks})


def modifier_vente(request, id):
    vente = get_object_or_404(Vente, id=id)
    clients = Client.objects.all()
    stocks = Stock.objects.all()

    if request.method == "POST":
        # preserve old stock/quantity before changes so we can adjust stock correctly
        old_stock = vente.stock
        old_q = vente.quantite_vendue

        # get selected client and optionally update its details if provided inline
        client = get_object_or_404(Client, id=request.POST['client'])
        # inline client update fields (optional)
        client_nom = request.POST.get('client_nom')
        client_prenom = request.POST.get('client_prenom')
        client_telephone = request.POST.get('client_telephone')
        client_adresse = request.POST.get('client_adresse')
        client_email = request.POST.get('client_email')
        if client_nom is not None and client_prenom is not None:
            # Save only non-empty updates to avoid overwriting with empty strings
            if client_nom.strip():
                client.nom = client_nom.strip()
            if client_prenom.strip():
                client.prenom = client_prenom.strip()
            if client_telephone is not None:
                client.telephone = client_telephone.strip()
            if client_adresse is not None:
                client.adresse = client_adresse.strip()
            if client_email is not None:
                client.email = client_email.strip()
            client.save()
        vente.client = client
        new_stock = get_object_or_404(Stock, id=request.POST['stock'])
        new_q = float(request.POST['quantite_vendue'])
        new_price = float(request.POST['prix_unitaire'])
        vente.stock = new_stock
        vente.quantite_vendue = new_q
        vente.prix_unitaire = new_price
        vente.date_vente = request.POST['date_vente']
        vente.montant_total = vente.quantite_vendue * vente.prix_unitaire
        vente.save()

        # Adjust stock inventories: add back the old sold quantity to old_stock, then subtract from new_stock
        try:
            strict_stock = request.POST.get('strict_stock') == '1'

            # restore old quantity to old_stock when different
            if old_stock and old_stock.id != new_stock.id:
                try:
                    old_orig = old_stock.quantite_disponible or 0
                    old_stock.quantite_disponible = old_orig + (old_q or 0)
                    old_stock.save()
                    # record restoration movement
                    try:
                        StockMovement.objects.create(stock=old_stock, vente=vente, change=(old_q or 0), reason='RESTORE', note=f'Restore from vente #{vente.id} modification')
                    except Exception:
                        pass
                except Exception:
                    pass

            # For new_stock, check availability
            new_orig = new_stock.quantite_disponible or 0
            if strict_stock and new_q > new_orig:
                messages.error(request, f"Stock insuffisant pour '{new_stock.produit}' (disponible: {new_orig}). Mise à jour annulée.")
                # rollback: reapply old_stock restoration if needed
                return redirect('modifier_vente', id=vente.id)

            if new_q > new_orig:
                deducted = new_orig
                new_stock.quantite_disponible = 0
                messages.warning(request, f"Vente mise à jour — stock insuffisant pour '{new_stock.produit}'. Quantité vendue limitée à {deducted} (stock mis à zéro).")
            else:
                deducted = new_q
                new_stock.quantite_disponible = new_orig - deducted

            new_stock.save()
            # record movement for new deduction
            try:
                StockMovement.objects.create(stock=new_stock, vente=vente, change=-deducted, reason='VENTE', note=f'Vente #{vente.id} updated')
            except Exception:
                pass
        except Exception:
            messages.warning(request, "Impossible de mettre à jour automatiquement les stocks liés à la vente.")

        # Handle facture create/update inline
        # look for existing facture linked to this vente (take first if multiple)
        try:
            facture = Facture.objects.filter(vente=vente).first()
        except Exception:
            facture = None

        # detect if facture fields were submitted
        create_facture_flag = request.POST.get('create_facture') == '1' or request.POST.get('numero_facture') or request.POST.get('montant')
        if create_facture_flag:
            numero_facture = request.POST.get('numero_facture') or ''
            date_emission = request.POST.get('date_emission') or date.today()
            montant = request.POST.get('montant')
            try:
                montant_val = float(montant) if montant not in (None, '') else float(vente.montant_total)
            except Exception:
                montant_val = float(vente.montant_total)
            mode_paiement = request.POST.get('mode_paiement') or 'LIQUIDE'
            statut = request.POST.get('statut') or 'ATTENTE'

            if facture:
                facture.numero_facture = numero_facture
                facture.date_emission = date_emission
                facture.montant = montant_val
                facture.mode_paiement = mode_paiement
                facture.statut = statut
                facture.save()
            else:
                Facture.objects.create(
                    vente=vente,
                    numero_facture=numero_facture,
                    date_emission=date_emission,
                    montant=montant_val,
                    mode_paiement=mode_paiement,
                    statut=statut
                )
        return redirect('liste_ventes')

    return render(request, 'vente/modifier.html', {
        'vente': vente,
        'clients': clients,
        'stocks': stocks
    })


def supprimer_vente(request, id):
    vente = get_object_or_404(Vente, id=id)
    vente.delete()
    return redirect('liste_ventes')


def details_vente(request, id):
    vente = get_object_or_404(Vente, id=id)
    return render(request, 'vente/details.html', {'vente': vente})


#---------------------------------- VUES POUR LES FACTURES ---------------------------------

def liste_factures(request):
    factures = Facture.objects.all()
    return render(request, 'facture/liste.html', {'factures': factures})


def ajouter_facture(request):
    ventes = Vente.objects.all()
    if request.method == "POST":
        vente = get_object_or_404(Vente, id=request.POST['vente'])
        numero_facture = request.POST['numero_facture']
        date_emission = request.POST.get('date_emission', date.today())
        montant = float(request.POST['montant'])
        mode_paiement = request.POST['mode_paiement']
        statut = request.POST['statut']

        Facture.objects.create(
            vente=vente,
            numero_facture=numero_facture,
            date_emission=date_emission,
            montant=montant,
            mode_paiement=mode_paiement,
            statut=statut
        )
        return redirect('liste_factures')

    return render(request, 'facture/ajouter.html', {'ventes': ventes})


def modifier_facture(request, id):
    facture = get_object_or_404(Facture, id=id)
    ventes = Vente.objects.all()

    if request.method == "POST":
        facture.vente = get_object_or_404(Vente, id=request.POST['vente'])
        facture.numero_facture = request.POST['numero_facture']
        facture.date_emission = request.POST['date_emission']
        facture.montant = float(request.POST['montant'])
        facture.mode_paiement = request.POST['mode_paiement']
        facture.statut = request.POST['statut']
        facture.save()
        return redirect('liste_factures')

    return render(request, 'facture/modifier.html', {
        'facture': facture,
        'ventes': ventes
    })


def supprimer_facture(request, id):
    facture = get_object_or_404(Facture, id=id)
    facture.delete()
    return redirect('liste_factures')


def details_facture(request, id):
    facture = get_object_or_404(Facture, id=id)
    return render(request, 'facture/details.html', {'facture': facture})


def print_facture(request, id):
    """Render a printer-friendly facture page including company name and logo."""
    facture = get_object_or_404(Facture, id=id)
    company = {
        'name': 'AgroData',
        'logo': 'images/logo12.jpg',
        'address': '',
        'phone': ''
    }
    return render(request, 'facture/print.html', {'facture': facture, 'company': company})


def download_facture(request, id):
    """Generate and return a PDF for the facture. Uses WeasyPrint if available, falls back to HTML.

    Returns an application/pdf response when possible, otherwise returns the rendered
    HTML page (useful when WeasyPrint isn't installed).
    """
    facture = get_object_or_404(Facture, id=id)
    company = {
        'name': 'AgroData',
        'logo': 'images/logo12.jpg',
        'address': '',
        'phone': ''
    }

    # Prefer a PDF-specific template; fall back to the printable HTML template
    template_names = ['facture/pdf.html', 'facture/print.html']
    for tmpl in template_names:
        try:
            html = render_to_string(tmpl, {'facture': facture, 'company': company}, request=request)
            break
        except Exception:
            html = None

    if not html:
        return HttpResponse("<h3>Impossible de générer la facture (template manquante)</h3>")

    try:
        # try to import and use WeasyPrint to build a proper PDF
        from weasyprint import HTML, CSS
        base_url = request.build_absolute_uri('/')
        pdf = HTML(string=html, base_url=base_url).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="facture_{facture.id}.pdf"'
        return response
    except Exception:
        # if WeasyPrint isn't available or fails, return the HTML so the user can print/save manually
        return HttpResponse(html)


def overview(request):
    """Combined overview for the vente module: clients, ventes and factures in tabs."""
    # small lists for quick overview, with optional pagination per tab
    clients_qs = Client.objects.order_by('-id')
    ventes_qs = Vente.objects.select_related('client', 'stock').order_by('-date_vente')
    factures_qs = Facture.objects.select_related('vente').order_by('-date_emission')

    # simple pagination (show 12 per tab)
    page_size = 12
    c_page = request.GET.get('cpage')
    v_page = request.GET.get('vpage')
    f_page = request.GET.get('fpage')

    c_p = Paginator(clients_qs, page_size).get_page(c_page)
    v_p = Paginator(ventes_qs, page_size).get_page(v_page)
    f_p = Paginator(factures_qs, page_size).get_page(f_page)

    context = {
        'clients_page': c_p,
        'ventes_page': v_p,
        'factures_page': f_p,
    }
    return render(request, 'vente/overview.html', context)

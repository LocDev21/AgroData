from django.shortcuts import render
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
import calendar
from datetime import date, timedelta, datetime
import json

# Import models for dashboard metrics
from producteurs.models import Producteur, Parcelle, Recolte
from transformation.models import Transformation
from stock.models import Stock
from vente.models import Client, Vente, Facture


def dashboard(request):
	"""Render a richer dashboard with detailed statistics and charts."""
	counts = {
		'producteurs': Producteur.objects.count(),
		'parcelles': Parcelle.objects.count(),
		'recoltes': Recolte.objects.count(),
		'transformations': Transformation.objects.count(),
		'stocks': Stock.objects.count(),
		'ventes': Vente.objects.count(),
		'clients': Client.objects.count(),
		'factures': Facture.objects.count(),
	}

	recent_ventes = Vente.objects.select_related('client', 'stock').order_by('-date_vente')[:8]
	recent_transformations = Transformation.objects.select_related('recolte').order_by('-date_debut')[:8]

	# determine period for top-products
	period = request.GET.get('period', '30d')
	start_param = request.GET.get('start')
	end_param = request.GET.get('end')

	# compute date range
	end_date = date.today()
	start_date = None
	if start_param and end_param:
		try:
			start_date = datetime.strptime(start_param, '%Y-%m-%d').date()
			end_date = datetime.strptime(end_param, '%Y-%m-%d').date()
		except Exception:
			start_date = None

	if not start_date:
		# map period codes to days
		if period == '7d':
			start_date = end_date - timedelta(days=7)
		elif period == '90d':
			start_date = end_date - timedelta(days=90)
		elif period == '365d':
			start_date = end_date - timedelta(days=365)
		else:  # default 30d
			start_date = end_date - timedelta(days=30)

	# Top products by revenue and quantity within the selected period
	sales_by_product_qs = (
		Vente.objects.filter(date_vente__gte=start_date, date_vente__lte=end_date)
		.values('stock__produit')
		.annotate(total_revenue=Sum('montant_total'), total_qty=Sum('quantite_vendue'))
		.order_by('-total_revenue')[:10]
	)
	sales_by_product = [
		{
			'produit': item['stock__produit'],
			'revenue': float(item['total_revenue'] or 0),
			'quantity': float(item['total_qty'] or 0),
		}
		for item in sales_by_product_qs
	]

	# Stocks aggregated by product
	stock_by_product_qs = (
		Stock.objects.values('produit')
		.annotate(total_stock=Sum('quantite_disponible'))
		.order_by('-total_stock')[:12]
	)
	stock_by_product = [
		{'produit': item['produit'], 'stock': float(item['total_stock'] or 0)}
		for item in stock_by_product_qs
	]

	# Transformations count by étape
	transformations_by_step_qs = (
		Transformation.objects.values('etape')
		.annotate(count=Count('id'))
	)
	transformations_by_step = [
		{'etape': item['etape'], 'count': item['count']}
		for item in transformations_by_step_qs
	]

	# Harvests by fruit
	harvests_by_fruit_qs = (
		Recolte.objects.values('fruit')
		.annotate(total=Sum('quantite'))
		.order_by('-total')[:10]
	)
	harvests_by_fruit = [
		{'fruit': item['fruit'], 'quantite': float(item['total'] or 0)}
		for item in harvests_by_fruit_qs
	]

	# Monthly sales for last 12 months
	today = date.today()
	start_month = (today.replace(day=1) - timedelta(days=365)).replace(day=1)
	monthly_qs = (
		Vente.objects.filter(date_vente__gte=start_month)
		.annotate(month=TruncMonth('date_vente'))
		.values('month')
		.annotate(total=Sum('montant_total'))
		.order_by('month')
	)
	# Build full 12-month labels and values
	months = []
	values = []
	# monthly_qs 'month' may be a datetime or a date depending on DB/backend.
	# Normalize to date objects for consistent lookup against `cur` (a date).
	month_map = {}
	for item in monthly_qs:
		m = item.get('month')
		if m is None:
			continue
		# If it's a datetime, convert to date(); if it's already a date, keep as-is.
		try:
			month_key = m.date() if hasattr(m, 'date') else m
		except Exception:
			month_key = m
		month_map[month_key] = float(item.get('total') or 0)
	# create ordered month list
	cur = start_month
	while cur <= today:
		months.append(cur.strftime('%b %Y'))
		values.append(month_map.get(cur, 0.0))
		# move to next month
		if cur.month == 12:
			cur = cur.replace(year=cur.year+1, month=1)
		else:
			cur = cur.replace(month=cur.month+1)

	# Top clients by revenue
	top_clients_qs = (
		Vente.objects.values('client__nom', 'client__prenom')
		.annotate(total_revenue=Sum('montant_total'))
		.order_by('-total_revenue')[:8]
	)
	top_clients = [
		{'client': f"{c['client__nom']} {c['client__prenom']}", 'revenue': float(c['total_revenue'] or 0)}
		for c in top_clients_qs
	]

	context = {
		'counts': counts,
		'recent_ventes': recent_ventes,
		'recent_transformations': recent_transformations,
		'sales_by_product': sales_by_product,
		'stock_by_product': stock_by_product,
		'transformations_by_step': transformations_by_step,
		'harvests_by_fruit': harvests_by_fruit,
		'monthly_sales_labels': months,
		'monthly_sales_values': values,
		'top_clients': top_clients,
		# period info for UI
		'period': period,
		'start_date': start_date,
		'end_date': end_date,
	}

	# JSON serialized arrays for safe injection into JS
	context.update({
		'sales_labels_json': json.dumps([p['produit'] for p in sales_by_product]),
		'sales_revenue_json': json.dumps([p['revenue'] for p in sales_by_product]),
		'monthly_labels_json': json.dumps(months),
		'monthly_values_json': json.dumps(values),
		'stock_labels_json': json.dumps([s['produit'] for s in stock_by_product]),
		'stock_values_json': json.dumps([s['stock'] for s in stock_by_product]),
		'trans_labels_json': json.dumps([t['etape'] for t in transformations_by_step]),
		'trans_values_json': json.dumps([t['count'] for t in transformations_by_step]),
		'harvest_labels_json': json.dumps([h['fruit'] for h in harvests_by_fruit]),
		'harvest_values_json': json.dumps([h['quantite'] for h in harvests_by_fruit]),
	})

	return render(request, 'dashboard/dashboard.html', context)

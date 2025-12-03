from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse


def login_view(request):
	"""Simple login view using Django's auth. Redirects to `next` or home on success."""
	if request.user.is_authenticated:
		return redirect('home')

	next_url = request.GET.get('next') or request.POST.get('next') or reverse('home')

	if request.method == 'POST':
		username = request.POST.get('username', '').strip()
		password = request.POST.get('password', '')
		user = authenticate(request, username=username, password=password)
		if user is not None:
			login(request, user)
			messages.success(request, f'Bienvenue, {user.get_full_name() or user.username}!')
			return redirect(next_url)
		else:
			messages.error(request, 'Identifiants invalides. Veuillez réessayer.')

	return render(request, 'login.html', {'next': next_url})


def logout_view(request):
	"""Logout and redirect to login page."""
	logout(request)
	messages.info(request, 'Vous avez été déconnecté.')
	return redirect('login')

# Create your views here.

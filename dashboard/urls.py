from django.urls import path
from . import views


urlpatterns = [
    # move dashboard to /dashboard/ so root ('/') can be used for login without conflict
    path('dashboard/', views.dashboard, name='home'),
]

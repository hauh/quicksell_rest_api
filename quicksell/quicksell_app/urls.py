"""Endpoints."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from quicksell_app import views


router = DefaultRouter()
router.register(r'listings', views.Listings, basename='listing')
router.register(r'users', views.Users, basename='user')

urlpatterns = router.urls + [
	path(r'auth/', include('rest_framework.urls', namespace='rest_framework')),
	path(r'token/', obtain_auth_token, name='auth-token')
]

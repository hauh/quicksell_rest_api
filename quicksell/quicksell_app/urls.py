"""Endpoints."""

from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from quicksell_app import views


router = DefaultRouter()

urlpatterns = router.urls + [
	path(r'auth/', obtain_auth_token, name='auth'),

	path(r'users/', views.UserList.as_view(), name='user-list'),
	path(r'users/new', views.UserCreate.as_view(), name='user-create'),
	path(r'users/edit', views.ProfileUpdate.as_view(), name='user-update'),
	path(r'users/<id>', views.ProfileDetail.as_view(), name='user-detail'),

	path(r'listings/new', views.ListingCreate.as_view(), name='listing-create'),
]

"""Endpoints."""

from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from quicksell_app import views


router = DefaultRouter()
# router.register(r'listings', views.Listing, basename='listing')

urlpatterns = router.urls + [
	path(r'users/', views.UserList.as_view(), name='user-list'),
	path(r'users/new', views.UserCreate.as_view(), name='user-create'),
	path(r'users/<id>/', views.UserDetail.as_view(), name='user-detail'),
	path(r'users/<id>/edit', views.UserUpdate.as_view(), name='user-update'),  # noqa
	path(r'auth/', obtain_auth_token, name='auth'),
]

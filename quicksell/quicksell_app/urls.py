"""Endpoints."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from quicksell_app import views


router = DefaultRouter()

urlpatterns = router.urls + [
	path('users/', include([
		path('', views.UserList.as_view(), name='user-list'),
		path('auth/', obtain_auth_token, name='auth'),
		path('new/', views.UserCreate.as_view(), name='user-create'),
		path('email/<str:base64email>/<str:token>/',
			views.EmailConfirm.as_view(), name='email-confirm'),
		path('profile/', views.ProfileUpdate.as_view(), name='profile-update'),
		path('password/', views.PasswordReset.as_view(), name='password-reset'),
		path('<uuid>/', views.ProfileDetail.as_view(), name='profile-detail'),
	])),

	path('listings/new', views.ListingCreate.as_view(), name='listing-create'),
]

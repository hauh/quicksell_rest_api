"""Endpoints."""

from django.urls import path, include

from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from quicksell_app import views
from quicksell_app.schema import schema_view


router = DefaultRouter()

urlpatterns = router.urls + [
	path('doc/', include([
		path('redoc/', schema_view.with_ui('redoc'), name='schema-redoc'),
		path('swagger/', schema_view.with_ui('swagger'), name='schema-swagger'),
	])),
	path('users/', include([
		path('', views.User.as_view(), name='user'),  # GET, POST, PATCH
		path('login/', obtain_auth_token, name='login'),  # POST
		# path('logout/', name='logout'),  # DELETE
		path('password/', views.Password.as_view(), name='password'),  # PUT, POST, DELETE  # noqa:E501
		path('email/<str:base64email>/<str:token>/',
			views.EmailConfirm.as_view(), name='email-confirm'),  # GET, PATCH
	])),
	path('profiles/', include([
		path('', views.Profile.as_view(), name='profile'),  # GET, PATCH
		path('<str:base64uuid>/',
			views.ProfileDetail.as_view(), name='profile-detail'),  # GET
	])),
	path('listings/', include([
		path('new/', views.ListingCreate.as_view(), name='listing-create'),  # POST
	]))
]

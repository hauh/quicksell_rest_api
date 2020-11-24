"""Endpoints."""

from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from quicksell_app import views
from quicksell_app.schema import schema_view

router = DefaultRouter()

urlpatterns = router.urls + [
	path('doc/', include([
		path('redoc/', schema_view.with_ui('redoc'), name='schema-redoc'),
		path('swagger/', schema_view.with_ui('swagger'), name='schema-swagger'),
	])),
	path('info/', views.Info.as_view(), name='info'),
	path('users/', include([
		path('', views.User.as_view(), name='user'),
		path('login/', obtain_auth_token, name='login'),
		# path('logout/', name='logout'),  # DELETE
		path('password/', views.Password.as_view(), name='password'),
		path('email/<str:base64email>/<str:token>/',
			views.EmailConfirm.as_view(), name='email-confirm'),
	])),
	path('profiles/', include([
		path('', views.Profile.as_view(), name='profile'),
		path('<str:base64uuid>/',
			views.ProfileDetail.as_view(), name='profile-detail'),
	])),
	path('listings/', include([
		path('', views.Listing.as_view(), name='listing'),
		path('<str:base64uuid>/',
			views.ListingDetail.as_view(), name='listing-detail'),
	]))
]

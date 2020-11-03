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
		path('', views.UserList.as_view(), name='user-list'),  # GET
		path('login/', obtain_auth_token, name='login'),  # POST
		# path('logout/', name='logout'),  # DELETE
		path('password/', views.PasswordUpdate.as_view(), name='password-update'),  # PUT, POST, DELETE  # noqa:E501
		path('email/', include([
			# path('', views.EmailUpdate.as_view(), name='email-update'),  # PATCH
			path('confirm/<str:base64email>/<str:token>/',
				views.EmailConfirm.as_view(), name='email-confirm'),  # GET, PATCH
		])),
		path('new/', views.UserCreate.as_view(), name='user-create'),  # POST
		path('profile/', views.ProfileUpdate.as_view(), name='profile-update'),  # PATCH  # noqa:E501
		path('<uuid>/', views.ProfileDetail.as_view(), name='profile-detail'),  # GET
	])),
	path('listings/', include([
		path('new/', views.ListingCreate.as_view(), name='listing-create'),  # POST
	]))
]

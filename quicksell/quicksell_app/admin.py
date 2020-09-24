"""Admin."""

from django.apps import apps
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from quicksell_app.models import User

admin.site.register(User, UserAdmin)
for model in apps.get_models():
	try:
		admin.site.register(model)
	except admin.sites.AlreadyRegistered:
		pass

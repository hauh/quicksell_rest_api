"""Admin."""

from django.apps import apps
from django.contrib import admin, auth
from django.urls import reverse
from django.utils.html import format_html
from mptt.admin import MPTTModelAdmin

from quicksell_app.models import Category, User


class UserAdmin(auth.admin.UserAdmin):
	"""Users management."""

	model = User

	list_display = ('email', 'is_staff', 'is_active', 'balance')
	list_filter = ('is_staff', 'is_active', 'balance')
	readonly_fields = (
		'id', 'date_joined', 'last_login',
		'profile_link', 'business_account_link'
	)
	ordering = ('id',)

	add_fieldsets = (
		(None, {'fields': (
			'email', 'password1', 'password2',
			'is_staff', 'is_superuser', 'is_active'
		)}),
	)
	fieldsets = (
		('Main Info', {'fields': ('id', 'email', 'password', 'balance')}),
		('Status', {'fields': ('is_email_verified', 'is_active', 'is_staff', 'is_superuser')}),  # noqa
		('Dates', {'fields': ('date_joined', 'last_login')}),
		('Profiles', {'fields': ('profile_link', 'business_account_link')}),
	)

	def _build_link(self, obj):
		# pylint: disable=protected-access
		return format_html(
			"<a href='{}'>{}</a>",
			reverse(
				f'admin:{obj._meta.app_label}_{obj._meta.model_name}_change',
				args=(obj.pk,)
			),
			obj.pk
		)

	def profile_link(self, user):
		return self._build_link(user.profile)
	profile_link.short_description = 'Profile'

	def business_account_link(self, user):
		return self._build_link(user.business_account)
	business_account_link.short_description = 'Business Account'


admin.site.register(User, UserAdmin)
admin.site.register(Category, MPTTModelAdmin)

for model in apps.get_models():
	try:
		admin.site.register(model)
	except admin.sites.AlreadyRegistered:
		pass

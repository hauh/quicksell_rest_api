"""User Models."""

import uuid
from datetime import date, datetime

from django.db import models
from django.contrib.auth.models import (
	AbstractBaseUser, PermissionsMixin, BaseUserManager)

from quicksell_app.utils import LowercaseEmailField


MESSAGES = {
	'not_unique':
		"A user with this email already exists.",
}


class UserManager(BaseUserManager):
	"""User Manager."""

	use_in_migrations = True

	def create_user(self, password, **fields):
		if not password:
			raise ValueError("Password required.")
		user = self.model(**fields)
		user.set_password(password)
		user.save()
		return user

	def create_superuser(self, **fields):
		fields['is_staff'] = True
		fields['is_superuser'] = True
		return self.create_user(**fields)

	def get_or_none(self, **kwargs):
		try:
			return self.get(**kwargs)
		except self.model.DoesNotExist:
			return None


class User(AbstractBaseUser, PermissionsMixin):
	"""User model."""

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ()

	objects = UserManager()

	email = LowercaseEmailField(  # replace with CIEmailField on Postgres
		unique=True, error_messages={'unique': MESSAGES['not_unique']})
	is_email_verified = models.BooleanField(default=False)
	is_active = models.BooleanField(default=True)
	is_staff = models.BooleanField(default=False)
	is_superuser = models.BooleanField(default=False)
	date_joined = models.DateTimeField(default=datetime.now, editable=False)
	balance = models.IntegerField(default=0)

	@property
	def profile(self):
		try:
			return self._profile
		except Profile.DoesNotExist:
			return Profile.objects.create(user=self)

	def __str__(self):
		if self.profile.full_name:
			return f"{self.email} ({self.profile.full_name})"
		return self.email

	def has_perm(self, perm, obj=None):
		return self.is_staff

	def has_module_perms(self, app_label):
		return self.is_staff

	def clean(self):
		super().clean()
		self.email = User.objects.normalize_email(self.email)


class Profile(models.Model):
	"""User profile info."""

	user = models.OneToOneField(
		User, related_name='_profile', primary_key=True, editable=False,
		on_delete=models.CASCADE
	)
	uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
	date_created = models.DateField(default=date.today, editable=False)
	full_name = models.CharField(max_length=100, blank=True)
	about = models.TextField(blank=True)
	online = models.BooleanField(default=True)
	rating = models.IntegerField(default=0)
	avatar = models.ImageField(null=True, upload_to='images/avatars')
	location = models.ForeignKey(
		'Location', related_name='+', null=True, on_delete=models.SET_NULL)

	def __str__(self):
		return str(self.user) + "'s profile."


class Location(models.Model):
	"""Location model."""

	longitude = models.DecimalField(max_digits=9, decimal_places=6)
	latitude = models.DecimalField(max_digits=9, decimal_places=6)


class BusinessAccount(models.Model):
	"""Business account of user."""

	user = models.OneToOneField(
		User, on_delete=models.CASCADE, related_name='business_account')
	is_active = models.BooleanField(default=False)
	expires = models.DateTimeField(null=True, blank=True)

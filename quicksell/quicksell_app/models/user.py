"""User Models."""

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import (
	AbstractBaseUser, PermissionsMixin, BaseUserManager)


MESSAGES = {
	'not_unique':
		"A user with this email already exists.",
}


class UserManager(BaseUserManager):
	"""User Manager."""

	use_in_migrations = True

	def create_user(self, email, password, **extra_fields):
		if not email or not password:
			raise ValueError("Missing required field.")
		email = self.normalize_email(email)
		user = self.model(email=email, **extra_fields)
		user.set_password(password)
		user.save()
		return user

	def create_superuser(self, email, password, **extra_fields):
		extra_fields['is_staff'] = True
		extra_fields['is_superuser'] = True
		return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
	"""User model."""

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ()

	objects = UserManager()

	email = models.EmailField(
		unique=True, null=False, blank=False,
		error_messages={'unique': MESSAGES['not_unique']}
	)
	is_email_verified = models.BooleanField(default=False)
	is_active = models.BooleanField(default=True)
	is_staff = models.BooleanField(default=False)
	is_superuser = models.BooleanField(default=False)
	date_joined = models.DateTimeField(default=timezone.now)
	balance = models.IntegerField(default=0)

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

	def save(self, *args, **kwargs):
		is_new = not self.pk
		super().save(*args, **kwargs)
		if is_new:
			UserProfile.objects.create(user=self)


class UserProfile(models.Model):
	"""User profile info."""

	user = models.OneToOneField(
		User, on_delete=models.CASCADE, primary_key=True,
		editable=False, related_name='profile'
	)
	full_name = models.CharField(max_length=100, blank=True)
	online = models.BooleanField(default=True)
	location = models.ForeignKey(
		'Location', null=True, blank=True, on_delete=models.SET_NULL)

	def __str__(self):
		return str(self.user)


class Location(models.Model):
	"""Location model."""

	longitude = models.DecimalField(max_digits=9, decimal_places=6)
	latitude = models.DecimalField(max_digits=9, decimal_places=6)


class BusinessAccount(models.Model):
	"""Business account of user."""

	user = models.OneToOneField(
		User, on_delete=models.CASCADE, related_name='business_account')
	expires = models.DateTimeField(null=False)

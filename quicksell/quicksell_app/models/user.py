"""Account-related models."""

import uuid
from datetime import date, datetime

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db.models import (
	CASCADE, BooleanField, CharField, DateField, DateTimeField, EmailField,
	ForeignKey, ImageField, IntegerChoices, IntegerField, OneToOneField,
	PositiveSmallIntegerField, TextField, UUIDField
)
from pyfcm import FCMNotification

from .basemodel import QuicksellManager, QuicksellModel


MESSAGES = {
	'unique': "A user with this email already exists.",
}


class LowercaseEmailField(EmailField):
	"""Case-insensitive email field."""

	def to_python(self, value):
		if not isinstance(value, str):
			return value
		return value.lower()


class UserManager(QuicksellManager):
	"""User Manager."""

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

	def get_by_natural_key(self, username):
		return self.get(**{self.model.USERNAME_FIELD: username})


class DeviceManager(QuicksellManager):
	"""Device manager."""

	MAX_FAILS = 10

	client = FCMNotification(settings.FCM_TOKEN)


class Device(QuicksellModel):
	"""User's device."""

	objects = DeviceManager()

	class Platform(IntegerChoices):
		"""Device platform."""

		other = 0, 'Other'
		android = 1, 'Android'
		ios = 2, 'iOS'

	fcm_id = TextField(db_index=True)
	is_active = BooleanField(default=True)
	fails_count = PositiveSmallIntegerField(default=0)
	platform = PositiveSmallIntegerField(choices=Platform.choices, default=0)

	def send_push_notification(self, **kwargs):
		response = self.objects.client.notify_single_device(
			registartion_token=self.fcm_id,
			timeout=kwargs.pop('timeout', 1),
			**kwargs
		)
		if 'error' in response['results'][0]:
			if self.fails_count >= DeviceManager.MAX_FAILS:
				self.update(active=False)
			else:
				self.update(fails_count=self.fails_count + 1)
		elif self.fails_count:
			self.update(fails_count=0)


class User(AbstractBaseUser, PermissionsMixin):
	"""User model."""

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ()

	objects = UserManager()

	email = LowercaseEmailField(unique=True, error_messages=MESSAGES)
	is_email_verified = BooleanField(default=False)
	is_active = BooleanField(default=True)
	is_staff = BooleanField(default=False)
	is_superuser = BooleanField(default=False)
	date_joined = DateTimeField(default=datetime.now, editable=False)
	balance = IntegerField(default=0)
	password_reset_code = IntegerField(null=True, blank=True)
	password_reset_request_time = DateTimeField(null=True, blank=True)
	device = ForeignKey(
		Device, related_name='owner', null=True, on_delete=CASCADE
	)

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

	def has_perm(self, _perm, _obj=None):
		return self.is_staff

	def has_module_perms(self, _app_label):
		return self.is_staff

	def clean(self):
		super().clean()
		self.email = User.objects.normalize_email(self.email)

	def notify(self, **kwargs):
		if self.device.is_active:
			self.device.send_push_notification(**kwargs)


class Profile(QuicksellModel):
	"""User profile info."""

	user = OneToOneField(
		User, related_name='_profile', primary_key=True,
		editable=False, on_delete=CASCADE
	)
	uuid = UUIDField(default=uuid.uuid4, unique=True, editable=False)
	date_created = DateField(default=date.today, editable=False)
	full_name = CharField(max_length=100, blank=True)
	about = TextField(blank=True)
	online = BooleanField(default=True)
	rating = IntegerField(default=0)
	avatar = ImageField(null=True, blank=True, upload_to='images/avatars')
	location = ForeignKey(
		'Location', related_name='+', null=True, blank=True, on_delete=SET_NULL
	)

	def __str__(self):
		return str(self.user) + "'s profile."


class Location(QuicksellModel):
	"""Location model."""

	longitude = DecimalField(max_digits=9, decimal_places=6)
	latitude = DecimalField(max_digits=9, decimal_places=6)


class BusinessAccount(QuicksellModel):
	"""Business account of user."""

	user = OneToOneField(User, related_name='business_account', on_delete=CASCADE)
	is_active = BooleanField(default=False)
	expires = DateTimeField(null=True, blank=True)

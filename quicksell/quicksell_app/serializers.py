"""User serilaizers."""

from uuid import UUID

from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth import password_validation

from rest_framework.serializers import ModelSerializer
from rest_framework.fields import Field, IntegerField
from rest_framework.exceptions import NotFound

from quicksell_app import models


class Base64UUIDField(Field):
	"""UUID to pretty base64 format."""

	def to_representation(self, value):
		return urlsafe_base64_encode(value.bytes)

	def to_internal_value(self, data):
		if isinstance(data, UUID):
			return data
		try:
			return UUID(bytes=urlsafe_base64_decode(data))
		except ValueError as err:
			raise NotFound() from err


class Profile(ModelSerializer):
	"""Users' Profile info."""

	uuid = Base64UUIDField(read_only=True)

	class Meta:
		model = models.Profile
		fields = (
			'uuid', 'date_created', 'full_name', 'about',
			'online', 'rating', 'avatar', 'location'
		)
		read_only_fields = ('uuid', 'date_created', 'online', 'rating', 'location')


class User(ModelSerializer):
	"""Users's account."""

	profile = Profile(read_only=True)

	class Meta:
		model = models.User
		fields = (
			'email', 'password', 'is_email_verified',
			'date_joined', 'balance', 'profile'
		)
		read_only_fields = ('is_email_verified', 'date_joined', 'balance', 'profile')
		extra_kwargs = {'password': {'write_only': True}}

	def validate_password(self, password):
		password_validation.validate_password(password)
		return password

	def create(self, validated_data):
		return self.Meta.model.objects.create_user(**validated_data)


class Listing(ModelSerializer):
	"""Listing info."""

	uuid = Base64UUIDField(read_only=True)
	price = IntegerField(min_value=0)
	seller = Profile(read_only=True)

	class Meta:
		model = models.Listing
		fields = (
			'uuid', 'title', 'description', 'price', 'category', 'status',
			'quantity', 'sold', 'views', 'date_created', 'date_expires',
			'location', 'condition_new', 'characteristics', 'seller', 'photos'
		)
		depth = 1
		read_only_fields = (
			'uuid', 'sold', 'views', 'date_created',
			'date_expires', 'seller', 'shop', 'photos'
		)
		ordering = 'created'

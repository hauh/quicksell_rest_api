"""User serilaizers."""

from django.utils.http import urlsafe_base64_encode
from django.contrib.auth import password_validation

from rest_framework.serializers import ModelSerializer
from quicksell_app import models


class QuicksellSerializer(ModelSerializer):
	"""Customized serialization."""

	def to_representation(self, obj):
		representation = super().to_representation(obj)
		if 'uuid' in representation:
			representation['uuid'] = urlsafe_base64_encode(obj.uuid.bytes)
		return representation


class Profile(QuicksellSerializer):
	"""Users' Profile info."""

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


class Listing(QuicksellSerializer):
	"""Listing info."""

	seller = Profile(read_only=True)

	class Meta:
		model = models.Listing
		fields = (
			'uuid', 'title', 'description', 'price', 'category', 'status',
			'quantity', 'sold', 'views', 'date_created', 'date_expires',
			'location', 'condition_new', 'characteristics', 'seller', 'photos'
		)
		depth = 1
		read_only_fields =\
			('uuid', 'sold', 'views', 'date_created', 'seller', 'shop', 'photos')
		ordering = 'created'

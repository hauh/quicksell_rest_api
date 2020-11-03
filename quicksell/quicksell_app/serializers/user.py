"""User serilaizers."""

from django.utils.http import urlsafe_base64_encode
from django.contrib.auth import password_validation

from rest_framework import serializers
from quicksell_app import models


class User(serializers.ModelSerializer):
	"""Users's account."""

	class Meta:
		model = models.User
		fields = ('email', 'password', 'is_email_verified', 'date_joined', 'balance')
		read_only_fields = ('is_email_verified', 'date_joined', 'balance')
		extra_kwargs = {'password': {'write_only': True}}

	def validate_password(self, password):
		password_validation.validate_password(password)
		return password

	def create(self, validated_data):
		return self.Meta.model.objects.create_user(**validated_data)


class Profile(serializers.ModelSerializer):
	"""Users' Profile info."""

	class Meta:
		model = models.Profile
		fields = (
			'uuid', 'date_created', 'full_name', 'about',
			'online', 'rating', 'avatar', 'location'
		)
		read_only_fields = ('uuid', 'date_created', 'online', 'rating', 'location')

	def to_representation(self, profile):
		representation = super().to_representation(profile)
		representation['uuid'] = urlsafe_base64_encode(profile.uuid.bytes)
		return representation

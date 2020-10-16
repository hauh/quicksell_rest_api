"""User serilaizers."""

from django.contrib.auth import password_validation
from rest_framework import serializers
from quicksell_app import models


class User(serializers.ModelSerializer):
	"""Users's account."""

	class Meta:
		model = models.User
		fields = (
			'id', 'email', 'password',
			'is_email_verified', 'date_joined', 'balance'
		)
		read_only_fields = ('id', 'is_email_verified', 'date_joined', 'balance')
		extra_kwargs = {'password': {'write_only': True}}

	def validate_password(self, password):
		password_validation.validate_password(password)
		return password


class Profile(serializers.ModelSerializer):
	"""Users' Profile info."""

	user_id = serializers.PrimaryKeyRelatedField(read_only=True)

	class Meta:
		model = models.Profile
		fields = (
			'user_id', 'full_name', 'about',
			'online', 'rating', 'avatar', 'location'
		)
		read_only_fields = ('user_id', 'online', 'rating', 'location')

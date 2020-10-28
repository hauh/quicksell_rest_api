"""User serilaizers."""


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

	def update(self, user, validated_data):
		if password := validated_data.pop('password', None):
			user.set_password(password)
		return super().update(user, validated_data)


class PasswordReset(serializers.Serializer):
	"""Reset password with code from email."""

	email = serializers.EmailField()
	code = serializers.IntegerField()


class Profile(serializers.ModelSerializer):
	"""Users' Profile info."""

	class Meta:
		model = models.Profile
		fields = (
			'uuid', 'date_created', 'full_name', 'about',
			'online', 'rating', 'avatar', 'location'
		)
		read_only_fields = ('uuid', 'date_created', 'online', 'rating', 'location')

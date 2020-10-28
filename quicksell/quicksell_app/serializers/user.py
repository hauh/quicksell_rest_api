"""User serilaizers."""


from django.contrib.auth import password_validation
from rest_framework import serializers, exceptions
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


class PasswordUpdate(serializers.ModelSerializer):
	"""Change User's password."""

	old_password = serializers.CharField(
		source='password', required=False, read_only=True)
	new_password = serializers.CharField(source='password', write_only=True)

	class Meta:
		model = models.User

	def validate_old_password(self, password):
		if self.instance.has_usable_password():
			if not self.instance.check_password(password):
				raise exceptions.NotAuthenticated("Wrong password.")
		return password

	def validate_new_password(self, password):
		password_validation.validate_password(password)
		return password

	def update(self, user, validated_data):
		user.set_password(validated_data['new_password'])
		return user


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

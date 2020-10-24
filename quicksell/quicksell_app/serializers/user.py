"""User serilaizers."""

from django.urls import reverse
from django.core.mail import send_mail
from django.contrib.auth import password_validation
from rest_framework import serializers
from quicksell_app import models
from quicksell_app.utils import email_verification_token_generator


class User(serializers.ModelSerializer):
	"""Users's account."""

	class Meta:
		model = models.User
		fields = (
			'uuid', 'email', 'password',
			'is_email_verified', 'date_joined', 'balance'
		)
		read_only_fields = ('uuid', 'is_email_verified', 'date_joined', 'balance')
		extra_kwargs = {'password': {'write_only': True}}

	def validate_password(self, password):
		password_validation.validate_password(password)
		return password

	def create(self, validated_data):
		user = self.Meta.model.objects.create_user(**validated_data)
		user.set_password(validated_data['password'])
		user.save()
		if request := self.context.get('request'):
			token = email_verification_token_generator.make_token(user)
			url = request.build_absolute_uri(
				reverse('email-confirm', args=(user.uuid, token)))
			send_mail(
				"Activate your Quicksell account",
				f"Click the link to confirm your email:\n{url}",
				None, recipient_list=[user.email]
			)
		return user

	def update(self, user, validated_data):
		if password := validated_data.pop('password', None):
			user.set_password(password)
		return super().update(user, validated_data)


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

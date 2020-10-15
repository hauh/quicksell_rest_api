"""User serilaizers."""

from django.contrib.auth import password_validation
from rest_framework.serializers import ModelSerializer
from quicksell_app import models


class User(ModelSerializer):
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

	def create(self, validated_data):
		return models.User.objects.create_user(**validated_data)


class UserProfile(ModelSerializer):
	"""Users' Profile info."""

	# listings = ListingPreview(many=True, read_only=True)

	class Meta:
		model = models.UserProfile
		fields = '__all__'
		read_only_fields = ('user', 'date_joined')

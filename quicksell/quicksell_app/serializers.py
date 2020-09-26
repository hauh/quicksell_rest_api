"""Serializers."""

from rest_framework.serializers import ModelSerializer
from quicksell_app import models


class ListingPreview(ModelSerializer):
	"""Short info about Listing."""

	class Meta:
		model = models.Listing
		fields = ('listing_id', 'title', 'category')
		read_only_fields = fields


class PublicUser(ModelSerializer):
	"""Users's info visible to anyone."""

	listings = ListingPreview(many=True, read_only=True)

	class Meta:
		model = models.User
		fields = (
			'user_id', 'username', 'first_name', 'last_name',
			'date_joined', 'last_login', 'online', 'listings'
		)
		read_only_fields = fields


class PrivateUser(ModelSerializer):
	"""Users's info only visible to self."""

	listings = ListingPreview(many=True, read_only=True)

	class Meta:
		model = models.User
		fields = (
			'user_id', 'username', 'email', 'first_name', 'last_name',
			'date_joined', 'last_login', 'online', 'listings', 'password'
		)
		read_only_fields = ('user_id', 'date_joined', 'last_login', 'listings')

	def create(self, validated_data):
		return models.User.objects.create_user(**validated_data)


class UserPreview(ModelSerializer):
	"""Short info about User."""

	class Meta:
		model = models.User
		fields = ('user_id', 'username', 'online')
		read_only_fields = fields


class Listing(ModelSerializer):
	"""Full Listing serializers."""

	owner = UserPreview(read_only=True)

	class Meta:
		model = models.Listing
		fields = (
			'listing_id', 'title', 'category', 'photo_filename',
			'date_created', 'closed', 'sold', 'owner'
		)
		read_only_fields = ('listing_id', 'created', 'owner')
		ordering = ('created')

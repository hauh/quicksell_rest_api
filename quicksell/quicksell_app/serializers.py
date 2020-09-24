"""Serializers."""

from rest_framework.serializers import ModelSerializer
from quicksell_app import models


class UserPreview(ModelSerializer):
	"""Short user info."""

	class Meta:
		model = models.User
		fields = ('user_id', 'username', 'online')
		read_only_fields = fields


class Listing(ModelSerializer):
	"""Serializer for listings."""

	owner = UserPreview(read_only=True)

	class Meta:
		model = models.Listing
		fields = (
			'listing_id', 'title', 'category', 'photo_filename',
			'date_created', 'closed', 'sold', 'owner'
		)
		read_only_fields = ('listing_id', 'created', 'owner')
		ordering = ('created')


class ShortListing(ModelSerializer):
	"""Short listing info."""

	class Meta:
		model = models.Listing
		fields = ('listing_id', 'title', 'category')
		read_only_fields = fields


class UserInfo(ModelSerializer):
	"""Full user info."""

	listings = ShortListing(many=True, read_only=True)

	class Meta:
		model = models.User
		fields = (
			'user_id', 'username', 'first_name', 'last_name',
			'date_joined', 'last_login', 'online', 'listings'
		)
		read_only_fields = ('user_id', 'date_joined', 'listings')

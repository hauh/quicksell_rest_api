"""Listing serializer."""

from rest_framework.serializers import ModelSerializer
from quicksell_app import models
from .user import UserProfile


class ListingPreview(ModelSerializer):
	"""Short info about Listing."""

	class Meta:
		model = models.Listing
		fields = ('listing_id', 'title', 'category')
		read_only_fields = fields


class Listing(ModelSerializer):
	"""Full Listing serializers."""

	owner = UserProfile(read_only=True)

	class Meta:
		model = models.Listing
		fields = (
			'listing_id', 'title', 'category', 'photo_filename',
			'date_created', 'closed', 'sold', 'owner'
		)
		read_only_fields = ('listing_id', 'created', 'owner')
		ordering = ('created')

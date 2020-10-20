"""Listing serializer."""

from rest_framework.exceptions import AuthenticationFailed
from rest_framework.serializers import ModelSerializer
from quicksell_app import models
from .user import Profile


class Listing(ModelSerializer):
	"""Listing serializer."""

	seller = Profile(read_only=True)

	class Meta:
		model = models.Listing
		fields = (
			'id', 'title', 'description', 'price', 'category', 'status',
			'quantity', 'sold', 'views', 'date_created', 'date_expires',
			'location', 'seller', 'shop', 'photos'
		)
		depth = 1
		read_only_fields =\
			('id', 'sold', 'views', 'date_created', 'seller', 'shop', 'photos')
		ordering = 'created'

	def create(self, validated_data):
		try:
			validated_data['seller'] = self.context['request'].user.profile
		except (KeyError, AttributeError) as err:
			raise AuthenticationFailed() from err
		return super().create(validated_data)

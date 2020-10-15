"""Listing view."""

from rest_framework.viewsets import ModelViewSet
from quicksell_app import models, serializers


class Listing(ModelViewSet):
	"""Get, create, modify, close listings."""

	queryset = models.Listing.objects
	serializer_class = serializers.Listing
	lookup_field = 'listing_id'

	def get_queryset(self):
		queryset = models.Listing.objects.all()
		request_params = self.request.query_params
		filters = {}
		if (user_id := request_params.get('user_id')):
			filters.update(owner__user_id=user_id)
		if not request_params.get('show_closed'):
			filters.update(closed=False)
		if not request_params.get('show_sold'):
			filters.update(sold=False)
		return queryset.filter(**filters)

	def perform_destroy(self, instance):
		instance.closed = True
		instance.save()

	def perform_create(self, serializer):
		serializer.save(owner=self.request.user)

"""Listing view."""

# from rest_framework import exceptions, permissions
from rest_framework.generics import (
	CreateAPIView, UpdateAPIView, ListAPIView, RetrieveAPIView
)
from quicksell_app import models, serializers


class ListingCreate(CreateAPIView):
	"""Create Listing."""

	queryset = models.Listing.objects
	serializer_class = serializers.Listing

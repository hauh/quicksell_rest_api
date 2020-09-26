"""Views."""

from rest_framework.generics import (
	CreateAPIView, UpdateAPIView, ListAPIView, RetrieveAPIView
)
from rest_framework.viewsets import ModelViewSet
from quicksell_app import models, serializers, permissions


class UserList(ListAPIView):
	"""List Users."""

	queryset = models.User.objects
	serializer_class = serializers.PublicUser


class UserDetail(RetrieveAPIView):
	"""Retrieve User."""

	queryset = models.User.objects
	lookup_field = 'username'

	def get_serializer_class(self):
		if (self.request.user.is_staff
		or self.request.user.username == self.request.query_params.get('username')):
			return serializers.PrivateUser
		return serializers.PublicUser


class UserCreate(CreateAPIView):
	"""Creates User."""

	queryset = models.User.objects
	serializer_class = serializers.PrivateUser
	permission_classes = ()


class UserUpdate(UpdateAPIView):
	"""Updates User."""

	queryset = models.User.objects
	serializer_class = serializers.PrivateUser
	permission_classes = (permissions.AccessProfile,)
	lookup_field = 'username'


class Listings(ModelViewSet):
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

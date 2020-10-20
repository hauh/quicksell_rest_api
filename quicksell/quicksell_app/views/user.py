"""Views."""

from rest_framework import exceptions, permissions
from rest_framework.response import Response
from rest_framework.generics import (
	CreateAPIView, UpdateAPIView, ListAPIView, RetrieveAPIView
)
from quicksell_app import models, serializers


class UserList(ListAPIView):
	"""List Users."""

	queryset = models.User.objects
	serializer_class = serializers.User


class UserCreate(CreateAPIView):
	"""Creates User."""

	queryset = models.User.objects
	serializer_class = serializers.User
	permission_classes = (permissions.AllowAny,)


class ProfileDetail(RetrieveAPIView):
	"""Retrieves User's Profile info."""

	queryset = models.User.objects
	serializer_class = serializers.Profile
	lookup_field = 'id'

	def retrieve(self, request, *args, **kwargs):
		user = self.get_object()
		if not user.is_active:
			raise exceptions.NotFound()
		return Response(self.get_serializer(user.profile).data)


class ProfileUpdate(UpdateAPIView):
	"""Updates User's Profile info."""

	http_method_names = ['patch', 'options']
	serializer_class = serializers.Profile

	def get_object(self):
		return self.request.user.profile

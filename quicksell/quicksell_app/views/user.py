"""Views."""

from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.generics import (
	CreateAPIView, UpdateAPIView, ListAPIView, RetrieveAPIView
)
from quicksell_app import models, serializers, permissions


class UserList(ListAPIView):
	"""List Users."""

	queryset = models.User.objects
	serializer_class = serializers.User


class UserDetail(RetrieveAPIView):
	"""Retrieve User."""

	queryset = models.User.objects
	serializer_class = serializers.User
	lookup_field = 'id'

	def retrieve(self, request, *args, **kwargs):
		instance = self.get_object()
		if not instance.is_active:
			raise exceptions.NotFound()
		serializer = self.get_serializer(instance)
		return Response(serializer.data)


class UserCreate(CreateAPIView):
	"""Creates User."""

	queryset = models.User.objects
	serializer_class = serializers.User
	permission_classes = ()


class UserUpdate(UpdateAPIView):
	"""Updates User."""

	queryset = models.User.objects
	serializer_class = serializers.User
	permission_classes = (permissions.AccessProfile,)
	lookup_field = 'username'

"""Views."""

from rest_framework import exceptions, permissions, status
from rest_framework.response import Response
from rest_framework.generics import (
	CreateAPIView, UpdateAPIView, ListAPIView, RetrieveAPIView
)
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.schemas.openapi import AutoSchema

from quicksell_app import models, serializers
from quicksell_app.utils import email_verification_token_generator


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


class ConfirmEmail(RetrieveAPIView, CreateAPIView):
	"""Checks User's email confirmation link."""

	queryset = models.User.objects
	serializer_class = serializers.User
	renderer_classes = (TemplateHTMLRenderer,)
	template_name = 'confirm_email.html'
	permission_classes = (permissions.AllowAny,)
	lookup_field = 'uuid'
	schema = AutoSchema(operation_id_base="ConfirmEmail")

	def get(self, *args, **kwargs):
		return Response()

	def post(self, request, uuid, token):
		user = self.get_object()
		if not email_verification_token_generator.check_token(user, token):
			return Response(status=status.HTTP_404_NOT_FOUND)
		user.is_email_verified = True
		user.save()
		return Response(status=status.HTTP_200_OK)

"""Views."""

from rest_framework import exceptions, permissions
from rest_framework.response import Response
from rest_framework.generics import (
	CreateAPIView, UpdateAPIView, ListAPIView, RetrieveAPIView)
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer

from quicksell_app import models, serializers
from quicksell_app.utils import (
	send_email_verification_link,
	email_verification_token_generator,
	base64_decode
)


class UserList(ListAPIView):
	"""List Users."""

	queryset = models.User.objects
	serializer_class = serializers.User


class UserCreate(CreateAPIView):
	"""Creates User."""

	queryset = models.User.objects
	serializer_class = serializers.User
	permission_classes = (permissions.AllowAny,)

	def perform_create(self, serializer):
		user = serializer.save()
		send_email_verification_link(self.request, user)


class ProfileDetail(RetrieveAPIView):
	"""Retrieves User's Profile info."""

	queryset = models.Profile.objects
	serializer_class = serializers.Profile
	lookup_field = 'uuid'

	def retrieve(self, *args, **kwargs):
		profile = self.get_object()
		if not profile.user.is_active:
			raise exceptions.NotFound()
		return Response(self.get_serializer(profile).data)


class ProfileUpdate(UpdateAPIView):
	"""Updates User's Profile info."""

	http_method_names = ['patch', 'options']
	serializer_class = serializers.Profile

	def get_object(self):
		return self.request.user.profile


class EmailConfirm(RetrieveAPIView, UpdateAPIView):
	"""Checks User's email confirmation link."""

	http_method_names = ['get', 'patch', 'options']
	queryset = models.User.objects
	serializer_class = serializers.User
	renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
	permission_classes = (permissions.AllowAny,)
	schema = None

	def get(self, *args, **kwargs):
		return Response(template_name='confirm_email.html')

	def partial_update(self, request, base64email, token):
		user = self.get_queryset().get_or_none(email=base64_decode(base64email))
		if not email_verification_token_generator.check_token(user, token):
			raise exceptions.ValidationError()
		user.is_email_verified = True
		user.save()
		return Response()

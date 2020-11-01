"""User and Profile Views."""

from rest_framework import exceptions, permissions, status
from rest_framework.response import Response
from rest_framework.generics import (
	GenericAPIView, CreateAPIView, UpdateAPIView, ListAPIView, RetrieveAPIView)
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer

from quicksell_app import models, serializers
from quicksell_app.misc import (
	send_email_verification_link, email_verification_token_generator,
	base64_decode
)


class UserList(ListAPIView):
	"""List Users."""

	queryset = models.User.objects
	serializer_class = serializers.User


class UserCreate(CreateAPIView):
	"""Create User."""

	queryset = models.User.objects
	serializer_class = serializers.User
	permission_classes = (permissions.AllowAny,)

	def perform_create(self, serializer):
		user = serializer.save()
		send_email_verification_link(self.request, user)


class ProfileDetail(RetrieveAPIView):
	"""User's Profile."""

	serializer_class = serializers.Profile
	lookup_field = 'uuid'

	def get_queryset(self):
		return models.Profile.objects.filter(user__is_active=True)


class ProfileUpdate(UpdateAPIView):
	"""Update User's Profile."""

	serializer_class = serializers.Profile

	def get_object(self):
		return self.request.user.profile


class EmailConfirm(GenericAPIView):
	"""Check User's email confirmation link."""

	queryset = models.User.objects
	serializer_class = serializers.User
	renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
	permission_classes = (permissions.AllowAny,)
	schema = None

	def get(self, *args, **kwargs):
		return Response(template_name='confirm_email.html')

	def patch(self, _request, base64email, token):
		user = self.get_queryset().get_or_none(email=base64_decode(base64email))
		if not email_verification_token_generator.check_token(user, token):
			raise exceptions.ValidationError()
		user.is_email_verified = True
		user.save()
		return Response(status=status.HTTP_200_OK)

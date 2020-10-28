"""Views."""

from random import randint
from datetime import datetime

from django.core.mail import send_mail

from rest_framework import exceptions, permissions, status
from rest_framework.response import Response
from rest_framework.generics import (
	CreateAPIView, UpdateAPIView, ListAPIView, RetrieveAPIView, DestroyAPIView)
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.authtoken.models import Token

from quicksell_app import models, serializers
from quicksell_app.misc import (
	PasswordResetDaily, PasswordResetHourly,
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


class PasswordUpdate(UpdateAPIView):
	"""Changes User's password."""

	http_method_names = ['put', 'options']
	queryset = models.User.objects
	serializer_class = serializers.PasswordUpdate

	def get_object(self):
		return self.request.user


class PasswordReset(UpdateAPIView, DestroyAPIView):
	"""Sends password reset code to email, then resets password with the code."""

	http_method_names = ['patch', 'delete', 'options']
	queryset = models.User.objects
	serializer_class = serializers.PasswordReset
	permission_classes = (permissions.AllowAny,)
	throttle_classes = (PasswordResetDaily, PasswordResetHourly)

	def validate_request(self, request_data, partial=True):
		serializer = self.get_serializer(data=request_data, partial=partial)
		serializer.is_valid(raise_exception=True)
		data = serializer.validated_data
		user = self.get_queryset().get_or_none(email=data['email'])
		return user, data

	def patch(self, request, *args, **kwargs):
		user, data = self.validate_request({'email': request.data.get('email')})
		if user:
			user.password_reset_code = randint(100000, 999999)
			user.password_reset_request_time = datetime.now()
			user.save()
			mail_text = (
				"Enter this code in Quicksell app to restore access to your account.\n"
				f"{user.password_reset_code}\n"
				"If you didn't request password reset, just ignore this message."
			)
		else:
			mail_text = (
				"Someone requested to reset password for their account, "
				"but there is no account associated with this email address. "
				"If that was you, try another address or contact support. "
				"Otherwise just ignore this message (or check our app)."
			)
		self.send_mail(mail_text, data['email'])
		return Response(status=status.HTTP_202_ACCEPTED)

	def delete(self, request, *args, **kwargs):
		user, data = self.validate_request(request.data, partial=False)
		if (not user or not user.password_reset_request_time
		or user.password_reset_code != data['code']
		or (datetime.now() - user.password_reset_request_time).seconds > 3600):
			raise exceptions.AuthenticationFailed()
		user.password_reset_code = None
		user.password_reset_request_time = None
		user.set_unusable_password()
		user.save()
		self.send_mail("Your password has been reset!", data['email'])
		Token.objects.filter(user=user).delete()
		token = Token.objects.create(user=user)
		return Response({'token': str(token)}, status=status.HTTP_200_OK)

	def send_mail(self, text, address):
		send_mail("Quicksell Account Password Reset",
			text, None, recipient_list=[address])


class ProfileDetail(RetrieveAPIView):
	"""Retrieves User's Profile info."""

	queryset = models.Profile.objects
	serializer_class = serializers.Profile
	lookup_field = 'uuid'

	def get(self, *args, **kwargs):
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

	def patch(self, request, base64email, token):
		user = self.get_queryset().get_or_none(email=base64_decode(base64email))
		if not email_verification_token_generator.check_token(user, token):
			raise exceptions.ValidationError()
		user.is_email_verified = True
		user.save()
		return Response(status=status.HTTP_200_OK)

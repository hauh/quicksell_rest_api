"""Change and reset password."""

from random import randint
from datetime import datetime

from django.contrib.auth import password_validation
from django.core.mail import send_mail as django_send_mail

from rest_framework.serializers import (
	Serializer, CharField, EmailField, IntegerField, SerializerMethodField)
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.response import Response
from rest_framework.status import (
	HTTP_200_OK, HTTP_202_ACCEPTED, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN)
from rest_framework.authtoken.models import Token

from drf_yasg.utils import swagger_auto_schema

from quicksell_app.models import User
from quicksell_app.misc import PasswordResetDaily, PasswordResetHourly


CODE_EXPIRY = 3600  # password reset code lifetime in seconds
MESSAGES = {
	'changed': "Your password has been changed!",
	'reset': "Your password has been reset!",
	'code_sent': (
		"Enter this code in the app to restore access to your account.\n{}\n"
		"If you didn't request password reset, just ignore this message."
	),
	'wrong_email': (
		"Someone requested to reset password for their account, "
		"but there is no account associated with this email address. "
		"If that was you, try another address or contact support. "
		"Otherwise just ignore this message (or check our app)."
	)
}


class ResetRequestSerializer(Serializer):
	"""POST"""
	email = EmailField(write_only=True)

	def update(self, user, _validated_data):
		user.password_reset_code = randint(100000, 999999)
		user.password_reset_request_time = datetime.now()
		user.save()
		return user


class PasswordChangeSerializer(Serializer):
	"""PUT"""
	old_password = CharField(write_only=True, required=False)
	new_password = CharField(write_only=True)

	def validate_new_password(self, new_pass):
		password_validation.validate_password(new_pass)
		return new_pass

	def update(self, user, validated_data):
		user.set_password(validated_data['new_password'])
		try:
			user.auth_token.delete()
		except Token.DoesNotExist:
			pass
		user.save()
		return user


class ResetPerformSerializer(Serializer):
	"""DELETE"""
	email = EmailField(write_only=True)
	code = IntegerField(write_only=True)
	token = SerializerMethodField()

	def update(self, user, _validated_data):
		user.password_reset_code = None
		user.password_reset_request_time = None
		user.set_unusable_password()
		try:
			user.auth_token.delete()
		except Token.DoesNotExist:
			pass
		user.save()
		return user

	def get_token(self, user):
		Token.objects.create(user=user)
		return str(user.auth_token)


class Password(GenericAPIView):
	"""Change password of a User."""

	queryset = User.objects
	throttle_classes = (PasswordResetDaily, PasswordResetHourly)
	serializer_classes = {
		'PUT': PasswordChangeSerializer,
		'POST': ResetRequestSerializer,
		'DELETE': ResetPerformSerializer,
	}

	def setup(self, request, *args, **kwargs):
		super().setup(request, *args, **kwargs)
		if request.method in ('POST', 'DELETE'):
			# pylint: disable=attribute-defined-outside-init
			self.permission_classes = (AllowAny,)

	def get_serializer_class(self):
		return self.serializer_classes[self.request.method]

	def get_object(self):
		if self.request.method == 'PUT':
			return self.request.user
		return self.filter_queryset(self.get_queryset()).get_or_none(
			email=self.request.data.get('email'))

	def validate_request(self, request_data):
		serializer = self.get_serializer(data=request_data)
		serializer.is_valid(raise_exception=True)
		serializer.instance = self.get_object()
		return serializer

	@swagger_auto_schema(
		operation_id='password-reset-request',
		operation_summary="Request reset User's password",
		operation_description=(
			"Notification mail will be sent to the email, "
			"with password reset code if user exists."
		),
		security=[],
		responses={HTTP_202_ACCEPTED: "Email will be sent shortly."}
	)
	def post(self, request, *args, **kwargs):
		serializer = self.validate_request(request.data)
		if serializer.instance:
			serializer.save()
			msg = MESSAGES['code_sent'].format(serializer.instance.password_reset_code)
		else:
			msg = MESSAGES['wrong_email']
		self.send_mail(msg, serializer.validated_data['email'])
		return Response(status=HTTP_202_ACCEPTED)

	@swagger_auto_schema(
		operation_id='password-update',
		operation_summary="Change User's password",
		operation_description=(
			"Old password is required "
			"if it wasn't reset before with DELETE method."
		),
		responses={
			HTTP_200_OK: "Password changed.",
			HTTP_401_UNAUTHORIZED: "Wrong password.",
		}
	)
	def put(self, request, *args, **kwargs):
		serializer = self.validate_request(request.data)
		if serializer.instance.has_usable_password():
			old_pass = serializer.validated_data.get('old_password')
			if not old_pass or not serializer.instance.check_password(old_pass):
				raise AuthenticationFailed("Wrong password.")
		serializer.save()
		self.send_mail(MESSAGES['changed'], serializer.instance.email)
		return Response(status=HTTP_200_OK)

	@swagger_auto_schema(
		operation_id='password-reset',
		operation_summary="Reset User's password",
		operation_description=(
			"If code matches email and it hasn't expired, User's password "
			"will become unusable and new authentication token will be present "
			"in reponse. Set new password with PUT method."
		),
		security=[],
		responses={
			HTTP_200_OK: ResetPerformSerializer,
			HTTP_401_UNAUTHORIZED: "Wrong code or email not found.",
			HTTP_403_FORBIDDEN: "Code expired."
		}
	)
	def delete(self, request, *args, **kwargs):
		serializer = self.validate_request(request.data)
		user = serializer.instance
		if not user or user.password_reset_code != serializer.validated_data['code']:
			raise AuthenticationFailed("Wrong code or email not found.")
		if (datetime.now() - user.password_reset_request_time).seconds > CODE_EXPIRY:
			raise PermissionDenied("Code expired.")
		serializer.save()
		self.send_mail(MESSAGES['reset'], user.email)
		return Response(serializer.data, status=HTTP_200_OK)

	@staticmethod
	def send_mail(message, address):
		django_send_mail("Quicksell Account Notification",
			message, None, recipient_list=[address])

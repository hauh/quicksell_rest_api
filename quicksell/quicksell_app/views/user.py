"""User endpoint."""

from django.urls import reverse
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.exceptions import ValidationError
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED

from drf_yasg.utils import swagger_auto_schema

from quicksell_app.models import User as user_model
from quicksell_app.serializers import User as user_serializer


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
	"""Tokens to confirm email."""

	def _make_hash_value(self, user, timestamp):
		return f"{user.pk}{user.is_email_verified}{timestamp}"


token_generator = EmailVerificationTokenGenerator()


class User(GenericAPIView):
	"""Account related actions."""

	queryset = user_model.objects
	serializer_class = user_serializer
	permission_classes = (IsAuthenticated,)

	def setup(self, request, *args, **kwargs):
		super().setup(request, *args, **kwargs)
		if request.method == 'POST':
			# pylint: disable=attribute-defined-outside-init
			self.permission_classes = (AllowAny,)

	@swagger_auto_schema(
		operation_id='user-details',
		operation_summary="Get User's account and Profile",
		operation_description=(
			"Returns authorized User's account info and that User's Profile."
		),
		responses={HTTP_200_OK: user_serializer}
	)
	def get(self, request, *args, **kwargs):
		return Response(self.get_serializer(request.user).data, status=HTTP_200_OK)

	@swagger_auto_schema(
		operation_id='user-create',
		operation_summary="Create User",
		operation_description=(
			"Creates new User with email and password. Email confirmation link "
			"will be sent to provided email."
		),
		security=[],
	)
	def post(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		email = serializer.validated_data['email']
		url_path = reverse('email-confirm', args=(
			urlsafe_base64_encode(email.encode()),
			token_generator.make_token(serializer.instance)
		))
		verification_link = request.build_absolute_uri(url_path)
		send_mail(
			"Activate Your Quicksell Account",
			"Click the link to confirm your email:\n" + verification_link,
			None, recipient_list=[email]
		)
		return Response(serializer.data, status=HTTP_201_CREATED)

	@swagger_auto_schema(
		operation_id='user-update',
		operation_summary='Update User',
		operation_description=(
			"Updates authorized User's with values from request body. "
			"Read-only fields will be ignored."
		)
	)
	def patch(self, request, *args, **kwargs):
		serializer = self.get_serializer(self.request.user, data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(serializer.data, status=HTTP_200_OK)


class EmailConfirm(GenericAPIView):
	"""Check User's email confirmation link."""

	queryset = user_model.objects
	serializer_class = user_serializer
	renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
	permission_classes = (AllowAny,)
	schema = None

	def get(self, *args, **kwargs):
		return Response(template_name='confirm_email.html')

	def patch(self, _request, base64email, token):
		email = urlsafe_base64_decode(base64email).decode()
		user = self.get_queryset().get_or_none(email=email)
		if not token_generator.check_token(user, token):
			raise ValidationError()
		user.is_email_verified = True
		user.save()
		return Response(status=HTTP_200_OK)

"""User endpoint."""

from django.urls import reverse
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import smart_bytes, smart_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from rest_framework.exceptions import ValidationError
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED

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

	def get(self, request, *args, **kwargs):
		return Response(self.get_serializer(request.user).data, status=HTTP_200_OK)

	def post(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		email = serializer.validated_data['email']
		url_path = reverse('email-confirm', args=(
			urlsafe_base64_encode(smart_bytes(email)),
			token_generator.make_token(serializer.instance)
		))
		verification_link = request.build_absolute_uri(url_path)
		send_mail(
			"Activate Your Quicksell Account",
			"Click the link to confirm your email:\n" + verification_link,
			None, recipient_list=[email]
		)
		return Response(serializer.data, status=HTTP_201_CREATED)

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
		email = smart_str(urlsafe_base64_decode(base64email))
		user = self.get_queryset().get_or_none(email=email)
		if not token_generator.check_token(user, token):
			raise ValidationError()
		user.is_email_verified = True
		user.save()
		return Response(status=HTTP_200_OK)

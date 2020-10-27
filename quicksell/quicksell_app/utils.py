"""Miscellaneous useful stuff."""

from django.urls import reverse
from django.db.models import EmailField
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import smart_bytes, smart_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.metadata import BaseMetadata


class LowercaseEmailField(EmailField):
	"""Case-insensitive email field."""

	def to_python(self, value):
		if not isinstance(value, str):
			return value
		return value.lower()


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
	"""Tokens to confirm email."""

	def _make_hash_value(self, user, timestamp):
		return f"{user.pk}{user.is_email_verified}{timestamp}"


class NoMetadata(BaseMetadata):
	"""The API is not for use outside of App."""

	def determine_metadata(self, *args, **kwargs):
		return (
			"This API is used with Quicksell App. "
			"Check it on App Store or Google Play!"
		)


def base64_encode(string):
	return urlsafe_base64_encode(smart_bytes(string))


def base64_decode(string):
	return smart_str(urlsafe_base64_decode(string))


def send_email_verification_link(request, user):
	url_path = reverse('email-confirm', args=(
		base64_encode(user.email),
		email_verification_token_generator.make_token(user)
	))
	verification_link = request.build_absolute_uri(url_path)
	send_mail(
		"Activate your Quicksell account",
		"Click the link to confirm your email:\n" + verification_link,
		None, recipient_list=[user.email]
	)


email_verification_token_generator = EmailVerificationTokenGenerator()
password_reset_token_generator = PasswordResetTokenGenerator()

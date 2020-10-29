"""Miscellaneous useful stuff."""

from django.urls import reverse
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import smart_bytes, smart_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from rest_framework.metadata import BaseMetadata
from rest_framework.throttling import UserRateThrottle


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


class PasswordResetDaily(UserRateThrottle):
	"""Rate limit on password reset endpoint per day."""
	scope = 'password_reset.day'


class PasswordResetHourly(UserRateThrottle):
	"""Rate limit on password reset endpoint per hour."""
	scope = 'password_reset.hour'


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
		"Activate Your Quicksell Account",
		"Click the link to confirm your email:\n" + verification_link,
		None, recipient_list=[user.email]
	)


email_verification_token_generator = EmailVerificationTokenGenerator()
password_reset_token_generator = PasswordResetTokenGenerator()

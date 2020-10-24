"""Miscellaneous useful stuff."""

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.metadata import BaseMetadata


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
	"""Tokens to confirm email."""

	def _make_hash_value(self, user, timestamp):
		return f"{user.pk}{timestamp}{user.is_email_verified}"


class NoMetadata(BaseMetadata):
	"""The API is not for use outside of App."""

	def determine_metadata(self, *args, **kwargs):
		return (
			"This API is used with Quicksell App. "
			"Check it on App Store or Google Play!"
		)


email_verification_token_generator = EmailVerificationTokenGenerator()

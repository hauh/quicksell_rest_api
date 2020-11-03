"""Miscellaneous useful stuff."""

from rest_framework.metadata import BaseMetadata
from rest_framework.throttling import UserRateThrottle


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

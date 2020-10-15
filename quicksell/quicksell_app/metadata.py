"""OPTIONS response."""

from rest_framework.metadata import BaseMetadata


class NoMetadata(BaseMetadata):
	"""The API is not for use outside of App."""

	def determine_metadata(self, *args, **kwargs):
		return (
			"This API is used with Quicksell App. "
			"Check it on App Store or Google Play!"
		)

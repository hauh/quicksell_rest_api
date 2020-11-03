"""Profile endpoint."""


from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from quicksell_app import serializers, models


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

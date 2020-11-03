"""Profile endpoint."""

from uuid import UUID
from django.utils.http import urlsafe_base64_decode

from rest_framework.response import Response
from rest_framework.serializers import (
	Serializer, CharField, DateField, IntegerField, BooleanField)
from rest_framework.generics import GenericAPIView
from rest_framework.exceptions import NotFound
from rest_framework.status import HTTP_200_OK

from quicksell_app.models import Profile as profile_model
from quicksell_app.serializers import Profile as profile_serializer


class ProfileQuerySerializer(Serializer):
	"""GET Profiles list query serializer."""

	order_by = CharField(required=False, default='-rating')
	full_name = CharField(required=False)
	registered_before = DateField(required=False)
	min_rating = IntegerField(required=False)
	online = BooleanField(required=False)

	def validate_order_by(self, order_by):
		if not order_by.removeprefix('-') in profile_serializer().get_fields():
			return self.fields['order_by'].default
		return order_by

	def to_representation(self, validated_data):
		filters = {}
		if full_name := validated_data.get('full_name'):
			filters['full_name__icontains'] = full_name
		if registered_before := validated_data.get('registered_before'):
			filters['date_created__lt'] = registered_before
		if min_rating := validated_data.get('min_rating'):
			filters['rating__gte'] = min_rating
		if online := validated_data.get('online'):
			filters['online'] = online
		return filters


class Profile(GenericAPIView):
	"""User's Profile."""

	queryset = profile_model.objects
	serializer_class = profile_serializer

	def get(self, request, *args, **kwargs):
		query_serializer = ProfileQuerySerializer(data=request.query_params)
		query_serializer.is_valid(raise_exception=True)
		queryset = self.filter_queryset(self.get_queryset())
		sorting_order = query_serializer.validated_data['order_by']
		filtered = queryset.filter(**query_serializer.data).order_by(sorting_order)
		if not filtered.exists():
			raise NotFound()
		pages = self.paginate_queryset(filtered)
		serializer = self.get_serializer(pages, many=True)
		return self.get_paginated_response(serializer.data)

	def patch(self, request, *args, **kwargs):
		serializer = self.get_serializer(request.user.profile, data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(serializer.data, status=HTTP_200_OK)


class ProfileDetail(GenericAPIView):
	"""Get Profile by UUID."""

	queryset = profile_model.objects
	serializer_class = profile_serializer
	lookup_field = 'uuid'

	def get(self, _request, base64uuid):
		try:
			uuid = UUID(bytes=urlsafe_base64_decode(base64uuid), version=4)
		except ValueError:
			raise NotFound()  # pylint: disable=raise-missing-from
		profile = self.filter_queryset(self.get_queryset()).get_or_none(uuid=uuid)
		if not profile:
			raise NotFound()
		return Response(self.get_serializer(profile).data, status=HTTP_200_OK)
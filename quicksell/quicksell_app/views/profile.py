"""Profile endpoint."""

from rest_framework.exceptions import NotFound
from rest_framework.fields import (
	BooleanField, CharField, DateField, IntegerField)
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.status import HTTP_200_OK

from drf_yasg.utils import swagger_auto_schema

from quicksell_app.serializers import Base64UUIDField
from quicksell_app.serializers import Profile as profile_serializer
from quicksell_app.models import Profile as profile_model


class ProfileQuerySerializer(Serializer):
	"""GET Profiles list query serializer."""

	orderable_fields = ('full_name', 'date_created', 'rating', 'location')
	default_ordering = '-rating'

	order_by = CharField(default=default_ordering)
	full_name = CharField(required=False)
	registered_before = DateField(required=False)
	min_rating = IntegerField(required=False)
	online = BooleanField(required=False, allow_null=True, default=None)

	def validate_order_by(self, order_by):
		if not order_by.removeprefix('-') in self.orderable_fields:
			return self.default_ordering
		return order_by

	def to_representation(self, validated_data):
		filters = {}
		if full_name := validated_data.get('full_name'):
			filters['full_name__icontains'] = full_name
		if registered_before := validated_data.get('registered_before'):
			filters['date_created__lt'] = registered_before
		if min_rating := validated_data.get('min_rating'):
			filters['rating__gte'] = min_rating
		if (online := validated_data.get('online')) is not None:
			filters['online'] = online
		return filters


class Profile(GenericAPIView):
	"""Get or edit user's Profile."""

	queryset = profile_model.objects
	serializer_class = profile_serializer

	@swagger_auto_schema(
		operation_id='profile-list',
		operation_summary="Get filtered list of Profiles",
		operation_description=(
			"Returns paginated list of Profiles fitered by query params. "
			"Ten profiles per page. Can be ordered by any of "
			f"{ProfileQuerySerializer.orderable_fields} fields. "
			"If field name prefixed with '-' ordering will be descending. "
			f"Default ordering is '{ProfileQuerySerializer.default_ordering}'."
		),
		query_serializer=ProfileQuerySerializer,
		security=[],
	)
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

	@swagger_auto_schema(
		operation_id='profile-update',
		operation_summary='Update Profile',
		operation_description=(
			"Updates authorized User's Profile with values from request body. "
			"Read-only fields will be ignored."
		)
	)
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

	@swagger_auto_schema(
		operation_id='profile-details',
		operation_summary='Get Profile',
		operation_description="Returns Profile of a Users by uuid from query.",
		security=[],
	)
	def get(self, _request, base64uuid):
		uuid = Base64UUIDField().to_internal_value(base64uuid)
		profile = self.filter_queryset(self.get_queryset()).get_or_none(uuid=uuid)
		if not profile:
			raise NotFound()
		return Response(self.get_serializer(profile).data, status=HTTP_200_OK)

"""Profile endpoint."""

from uuid import UUID
from django.utils.http import urlsafe_base64_decode

from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.fields import CharField, IntegerField
from rest_framework.generics import GenericAPIView
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.status import (
	HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT)

from drf_yasg.utils import swagger_auto_schema, no_body

from quicksell_app.models import Listing as listing_model
from quicksell_app.serializers import Listing as listing_serializer


class ListingQuerySerializer(Serializer):
	"""GET Listings list query serializer."""

	orderable_fields = (
		'title', 'price', 'quantity', 'views', 'date_created', 'location',)
	default_ordering = '-price'

	order_by = CharField(default=default_ordering)
	min_price = IntegerField(min_value=0, required=False)
	max_price = IntegerField(min_value=0, required=False)
	title = CharField(required=False)

	def validate_order_by(self, order_by):
		if not order_by.removeprefix('-') in self.orderable_fields:
			return self.default_ordering
		return order_by

	def to_representation(self, validated_data):
		filters = {}
		if title := validated_data.get('title'):
			filters['title__icontains'] = title
		if min_price := validated_data.get('min_price'):
			filters['price__gte'] = min_price
		if max_price := validated_data.get('max_price'):
			filters['price__lte'] = max_price
		return filters


class Listing(GenericAPIView):
	"""Get list of filtered Listings or create one."""

	queryset = listing_model.objects
	serializer_class = listing_serializer

	@swagger_auto_schema(
		operation_id='listing-list',
		operation_summary="Get filtered list of Listings",
		operation_description=(
			"Returns paginated list of Listings fitered by query params. "
			"Ten listings per page. Can be ordered by any of "
			f"{ListingQuerySerializer.orderable_fields} fields. "
			"If field name prefixed with '-' ordering will be descending. "
			f"Default ordering is '{ListingQuerySerializer.default_ordering}'."
		),
		query_serializer=ListingQuerySerializer,
		security=[],
	)
	def get(self, request, *args, **kwargs):
		query_serializer = ListingQuerySerializer(data=request.query_params)
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
		operation_id='listing-create',
		operation_summary="Create Listing",
		operation_description=(
			"Creates new Listing with parameters from request body."
		),
	)
	def post(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save(seller=request.user.profile)
		return Response(serializer.data, status=HTTP_201_CREATED)


class ListingDetail(GenericAPIView):
	"""Get, edit or delete Listing."""

	queryset = listing_model.objects
	serializer_class = listing_serializer
	lookup_field = 'uuid'

	def get_object(self, base64uuid):
		try:
			uuid = UUID(bytes=urlsafe_base64_decode(base64uuid), version=4)
		except ValueError:
			raise NotFound()  # pylint: disable=raise-missing-from
		return self.filter_queryset(self.get_queryset()).get(uuid=uuid)

	def check_object_permissions(self, request, listing):
		if request.user.profile != listing.seller:
			raise PermissionDenied()

	@swagger_auto_schema(
		operation_id='listing-details',
		operation_summary='Get Listing',
		operation_description="Returns Listing by uuid from query.",
		security=[],
	)
	def get(self, _request, base64uuid):
		serializer = self.get_serializer(self.get_object(base64uuid))
		return Response(serializer.data, status=HTTP_200_OK)

	@swagger_auto_schema(
		operation_id='listing-update',
		operation_summary='Update Listing',
		operation_description=(
			"Updates Listing by uuid from query with request data "
			"if it was created by authorized user."
		),
	)
	def patch(self, request, base64uuid):
		listing = self.get_object(base64uuid)
		self.check_object_permissions(request, listing)
		serializer = self.get_serializer(listing, data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(serializer.data, status=HTTP_200_OK)

	@swagger_auto_schema(
		operation_id='listing-delete',
		operation_summary="Delete Listing",
		operation_description=(
			"Deletes Listing by uuid from query "
			"if it was created by authorized user."
		),
		request_body=no_body,
	)
	def delete(self, request, base64uuid):
		listing = self.get_object(base64uuid)
		self.check_object_permissions(request, listing)
		listing.delete()
		return Response(status=HTTP_204_NO_CONTENT)

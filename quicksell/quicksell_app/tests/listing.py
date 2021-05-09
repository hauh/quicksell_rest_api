"""Listings tests."""

from functools import partial

from django.urls import reverse
from model_bakery import baker
from rest_framework.status import (
	HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST,
	HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
)


from quicksell_app import models
from quicksell_app.models.listing import Category
from quicksell_app.serializers import Listing as listing_serializer
from .basetest import BaseTest


class BaseListingsTest(BaseTest):
	"""Common things for endpoints at `api/listings/`."""

	url_listings = reverse('listing')
	url_details = partial(reverse, 'listing-detail')

	fields_to_test = tuple(
		field for field in listing_serializer.Meta.fields
		if field not in listing_serializer.Meta.read_only_fields
	)

	def setUp(self):
		self.make_user()


class TestListingCreation(BaseListingsTest):
	"""POST, GET /api/listings/"""

	def setUp(self):
		super().setUp()
		self.category = baker.make('Category', name='test_cat', rght=None)
		self.listing_data = {
			'title': "Test",
			'price': 100,
			'location': {
				'coordinates': "12.3456, 65.4321",
				'address': "Test avenue 42"
			},
			'category': self.category.serialize(),
		}

	def test_query_listings(self):
		check_result = partial(self.query_paginated_result, self.url_listings)
		q = 111
		make = partial(baker.make, models.Listing, _quantity=q, make_m2m=True)
		make(price=0, title="++TEST++")
		make(price=10, condition_new=True)
		make(price=20, seller=self.user.profile)
		make(price=30, category=self.category)
		max_q = q * 4
		self.assertEqual(models.Listing.objects.count(), max_q)

		check_result({}, max_q)
		check_result({'min_price': 10}, max_q - q)
		check_result({'max_price': 10}, max_q - q * 2)
		check_result({'min_price': 10, 'max_price': 10}, q)
		check_result({'min_price': 20, 'max_price': 10}, 0)

		check_result({'title': "++TEST++"}, q)
		check_result({'title': "+TEST+"}, q)
		check_result({'title': "--NOPE--"}, 0)

		check_result({'condition_new': True}, q)
		check_result({'condition_new': False}, max_q - q)

		uuid = self.base64uuid(self.user.profile.uuid)
		check_result({'seller': uuid}, q)
		check_result({'seller': uuid, 'max_price': 10}, 0)
		check_result({'seller': uuid, 'min_price': 10}, q)

		check_result({'category': "NotExist"}, 0)
		check_result({'category': self.category.name}, q)
		check_result({'max_price': 25, 'category': self.category.name}, 0)
		check_result({'min_price': 25, 'category': self.category.name}, q)

		data = {'min_price': 5, 'order_by': 'price'}
		first_page, last_page = check_result(data, max_q - q)
		self.assertEqual(first_page.data['results'][0]['price'], 10)
		self.assertEqual(last_page.data['results'][-1]['price'], 30)

		data = {'max_price': 15, 'order_by': '-rating'}
		first_page, last_page = check_result(data, max_q - q * 2)
		self.assertEqual(first_page.data['results'][0]['price'], 10)
		self.assertEqual(last_page.data['results'][-1]['price'], 0)

	def test_create(self):
		# who are you?
		self.POST(self.url_listings, HTTP_401_UNAUTHORIZED, self.listing_data)
		self.assertEqual(models.Listing.objects.count(), 0)
		# successful creation
		self.authorize()
		response = self.POST(self.url_listings, HTTP_201_CREATED, self.listing_data)
		self.assertEqual(models.Listing.objects.count(), 1)
		self.assertDictContainsSubset(self.listing_data, response.data)

	def test_categories(self):
		self.authorize()
		self.POST(self.url_listings, HTTP_201_CREATED, self.listing_data)
		self.assertEqual(models.Listing.objects.count(), 1)
		# can no longer assign to parent categories if it has children
		child = baker.make('Category', name='child', parent=self.category)
		Category.objects.rebuild()
		self.POST(self.url_listings, HTTP_400_BAD_REQUEST, self.listing_data)
		self.assertEqual(models.Listing.objects.count(), 1)
		# children category are ok though
		self.listing_data['category'] = child.serialize()
		response = self.POST(self.url_listings, HTTP_201_CREATED, self.listing_data)
		self.assertEqual(models.Listing.objects.count(), 2)
		self.assertIn('uuid', response.data)
		listing_url = self.url_details(args=(response.data['uuid'],))
		# if category was deleted
		child.delete()
		response = self.GET(listing_url, HTTP_200_OK)
		self.assertIn('category', response.data)
		self.assertEqual(response.data['category'], '__uncategorized__')
		# parent category is now acceptable again
		self.listing_data['category'] = self.category.serialize()
		self.POST(self.url_listings, HTTP_201_CREATED, self.listing_data)
		self.assertEqual(models.Listing.objects.count(), 3)

	def test_invalid_creation(self):
		self.authorize()
		self.POST(self.url_listings, HTTP_201_CREATED, self.listing_data)
		self.assertEqual(models.Listing.objects.count(), 1)
		# missing required fields
		for field in ('price', 'title', 'category', 'location'):
			invalid_data = {**self.listing_data}
			invalid_data.pop(field)
			self.POST(self.url_listings, HTTP_400_BAD_REQUEST, invalid_data)
		# invalid values
		for invalid in (
			{'price': -1}, {'price': None},
			{'title': ""}, {'title': None},
			{'condition_new': None},
			{'category': None}, {'category': "DoesNotExist"},
			{'location': None}, {'location': "improper_format"}
		):
			invalid_data = {**self.listing_data, **invalid}
			self.POST(self.url_listings, HTTP_400_BAD_REQUEST, invalid_data)
		self.assertEqual(models.Listing.objects.count(), 1)


class TestListingEdit(BaseListingsTest):
	"""PATCH, DELETE api/listings/<base64uuid>"""

	listing = None

	def setUp(self):
		super().setUp()
		self.listing = baker.make('Listing', seller=self.user.profile)
		uuid = self.base64uuid(self.listing.uuid)
		self.listing_url = self.url_details(args=(uuid,))

	def test_update(self):
		self.authorize()
		# update fields one by one
		for field, new_value in (
			('price', self.listing.price + 100),
			('condition_new', not self.listing.condition_new),
			('title', "New Title"),
			('description', "New description."),
			('category', baker.make('Category', name='valid', rght=None).serialize()),
			('location', {'coordinates': "12.345678, 87.654321", 'address': "Addr"})
		):
			response = self.PATCH(self.listing_url, HTTP_200_OK, {field: new_value})
			self.assertIn(field, response.data)
			self.assertEqual(response.data[field], new_value)
			self.listing.refresh_from_db()
			serialized = listing_serializer(self.listing)
			self.assertEqual(serialized.data[field], new_value)
		# update all at once
		new_category = baker.make('Category', name='another_valid_cat', rght=None)
		alter = baker.prepare('Listing', category=new_category)
		serialized_alter = listing_serializer(alter)
		data = {field: serialized_alter.data[field] for field in self.fields_to_test}
		patch_response = self.PATCH(self.listing_url, HTTP_200_OK, data)
		self.assertDictContainsSubset(data, patch_response.data)
		get_response = self.GET(self.listing_url, HTTP_200_OK)
		self.assertEqual(patch_response.data, get_response.data)

	def test_invalid_update(self):
		# who are you?
		self.PATCH(self.listing_url, HTTP_401_UNAUTHORIZED, {'price': 1})
		# not yours!
		self.authorize()
		anothers_listing = baker.make('Listing', make_m2m=True)
		self.assertEqual(models.Listing.objects.count(), 2)
		uuid = self.base64uuid(anothers_listing.uuid)
		self.PATCH(self.url_details(args=(uuid,)), HTTP_403_FORBIDDEN, {'price': 1})
		# invalid data
		for field, invalid_value in (
			('price', -1), ('price', None),
			('title', ""), ('title', None),
			('category', -1), ('category', None),
			('condition_new', None),
		):
			data = {field: invalid_value}
			self.PATCH(self.listing_url, HTTP_400_BAD_REQUEST, data)
			self.listing.refresh_from_db()
			self.assertNotEqual(getattr(self.listing, field), invalid_value)

	def test_delete(self):
		self.assertEqual(models.Listing.objects.count(), 1)
		self.DELETE(self.listing_url, HTTP_401_UNAUTHORIZED)
		self.assertEqual(models.Listing.objects.count(), 1)
		self.authorize()
		self.DELETE(self.listing_url, HTTP_204_NO_CONTENT)
		self.assertEqual(models.Listing.objects.count(), 0)
		anothers_listing = baker.make('Listing', make_m2m=True)
		self.assertEqual(models.Listing.objects.count(), 1)
		uuid = self.base64uuid(anothers_listing.uuid)
		self.DELETE(self.url_details(args=(uuid,)), HTTP_403_FORBIDDEN)
		self.assertEqual(models.Listing.objects.count(), 1)


class TestListingFull(BaseListingsTest):
	"""Test all Listing actions together."""

	def test_listing_actions(self):
		category1 = baker.make('Category', name='cat1', rght=None)
		category2 = baker.make('Category', name='cat2', rght=None)
		listings_urls = []
		users = []
		for q in range(1, 11):
			user = baker.make(self.user_model)
			users.append(user)
			self.authorize(user)
			# check existing listings
			for url in listings_urls:
				response = self.GET(url, HTTP_200_OK)
			# create new listing
			prepared_data = listing_serializer(
				baker.prepare('Listing', category=category1)
			).data
			data = {field: prepared_data[field] for field in self.fields_to_test}
			response = self.POST(self.url_listings, HTTP_201_CREATED, data)
			self.assertDictContainsSubset(data, response.data)
			self.assertEqual(models.Listing.objects.count(), q)
			# edit listing
			url = self.url_details(args=(response.data['uuid'],))
			listings_urls.append(url)
			alter_listing = baker.prepare('Listing', price=12345, category=category2)
			prepared_data = listing_serializer(alter_listing).data
			for field in self.fields_to_test:
				response = self.PATCH(url, HTTP_200_OK, {field: prepared_data[field]})
				if field in self.fields_to_test:
					self.assertEqual(prepared_data[field], response.data[field])
				else:
					self.assertNotEqual(prepared_data[field], response.data[field])
			# search for some listing
			query_data = {
				'min_price': 12345,
				'max_price': 12345,
				'category': category2.name,
				'order_by': '-category'
			}
			self.query_paginated_result(self.url_listings, query_data, q)
		# then delete
		how_many = len(listings_urls)
		self.assertEqual(len(users), how_many)
		for user, url in zip(users, listings_urls):
			self.authorize(user)
			self.DELETE(url, HTTP_204_NO_CONTENT)
			self.GET(url, HTTP_404_NOT_FOUND)
			how_many -= 1
			self.assertEqual(models.Listing.objects.count(), how_many)

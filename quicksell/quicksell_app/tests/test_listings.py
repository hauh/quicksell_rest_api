"""Listings testing."""

from model_bakery import baker
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.test import APITestCase

from quicksell_app import models


class UsersTests(APITestCase):
	"""Testing users' actions."""

	url_auth = reverse('auth')
	url_listing_create = reverse('listing-create')

	fields_create = ('title', 'price', 'category', 'status')
	default_fields = {
		'description': None,
		'status': 0,
		'quantity': 1,
		'sold': 0,
		'views': 0,
		'location': None,
		'shop': 'Shop Name',
		'photos': []
	}
	generated_fields = ('id', 'date_created', 'date_expires', 'seller')

	def _authorized_user(self):
		user = baker.make(models.User)
		auth_data = {'username': user.email, 'password': user.password}
		user.set_password(user.password)
		user.save()
		response = self.client.post(self.url_auth, auth_data)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.client.credentials(HTTP_AUTHORIZATION='Token ' + response.data['token'])
		return user

	def _listing_data(self):
		listing = baker.prepare(models.Listing)
		return {key: getattr(listing, key) for key in self.fields_create}

	def test_create_unauthorized(self):
		response = self.client.post(self.url_listing_create, self._listing_data())
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_create_missing_info(self):
		self._authorized_user()
		for required_field in self.fields_create:
			listing_data = self._listing_data().pop(required_field)
			response = self.client.post(self.url_listing_create, listing_data)
			self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_create(self):
		user = self._authorized_user()
		listing = self._listing_data()
		response = self.client.post(self.url_listing_create, listing)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertDictContainsSubset(listing, response.data)
		self.assertDictContainsSubset(self.default_fields, response.data)
		for other_field in self.generated_fields:
			self.assertIn(other_field, response.data)
		self.assertEqual(response.data['seller']['user_id'], user.id)
		date_created = parse_datetime(response.data['date_created'])
		date_expires = parse_datetime(response.data['date_expires'])
		self.assertTrue((date_expires - date_created).days == 30)

"""Common testing patterns."""

from django.conf import settings

from rest_framework.test import APITestCase
from rest_framework.settings import api_settings
from rest_framework.authtoken.models import Token
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from model_bakery import baker

from quicksell_app.models import User
from quicksell_app.serializers import Base64UUIDField


class BaseTest(APITestCase):
	"""Base class for API tests."""

	user_model = User
	emails_from = settings.DEFAULT_FROM_EMAIL
	page_size = api_settings.PAGE_SIZE

	pagination_fields = ('count', 'next', 'previous', 'results')

	def make_request(self, request, url, expected_status, data):
		response = request(url, data)
		info = (url, data, response.data)
		self.assertEqual(response.status_code, expected_status, info)
		return response

	def GET(self, url, expected_status, data=None):
		return self.make_request(self.client.get, url, expected_status, data)

	def POST(self, url, expected_status, data=None):
		return self.make_request(self.client.post, url, expected_status, data)

	def PUT(self, url, expected_status, data=None):
		return self.make_request(self.client.put, url, expected_status, data)

	def PATCH(self, url, expected_status, data=None):
		return self.make_request(self.client.patch, url, expected_status, data)

	def DELETE(self, url, expected_status, data=None):
		return self.make_request(self.client.delete, url, expected_status, data)

	user = None
	user_pass = None

	def make_user(self):
		self.user = baker.make(self.user_model, make_m2m=True)
		self.assertEqual(self.user_model.objects.count(), 1)
		self.user_pass = self.user.password
		self.user.set_password(self.user.password)
		self.user.save()
		self.user.refresh_from_db()

	def base64uuid(self, uuid_value):
		return Base64UUIDField().to_representation(uuid_value)

	def authorize(self, user=None):
		token = Token.objects.get_or_create(user=user or self.user)
		self.client.credentials(HTTP_AUTHORIZATION='Token ' + token[0].key)

	def query_paginated_result(self, url, params, count):
		if count == 0:
			return self.GET(url, HTTP_404_NOT_FOUND, params)
		first_page = last_page = self.GET(url, HTTP_200_OK, params)
		self.assertTupleEqual(self.pagination_fields, tuple(first_page.data))
		self.assertIsNone(first_page.data['previous'])
		self.assertEqual(count, first_page.data['count'], params)
		for _ in range((count - 1) // self.page_size):
			next_page_url = last_page.data['next']
			self.assertIsNotNone(next_page_url, count)
			last_page = self.GET(next_page_url, HTTP_200_OK)
		self.assertIsNone(last_page.data['next'])
		return first_page, last_page

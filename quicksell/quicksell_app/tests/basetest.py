"""Common testing patterns."""

from django.conf import settings

from rest_framework.test import APITestCase
from rest_framework.settings import api_settings
from rest_framework.authtoken.models import Token

from model_bakery import baker

from quicksell_app.models import User


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

	def authorize(self):
		token = baker.make(Token, user=self.user)
		self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

"""Common testing patterns."""

from datetime import date
from uuid import UUID

from django.core.files import File
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from model_bakery import baker

from quicksell_app.models import User


class BaseTest(APITestCase):
	"""Base class for API tests."""

	user_model = User
	user = None

	def make_request(self, request, url, expected_status, data):
		response = request(url, data)
		self.assertEqual(response.status_code, expected_status, (url, data))
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

	def field_by_field_compare(self, response_data, obj, fields):
		for field in fields:
			response_value = response_data.pop(field)
			db_value = getattr(obj, field)
			try:
				self.assertEqual(response_value, db_value, field)
			except AssertionError:
				if isinstance(db_value, date):
					self.assertEqual(response_value, db_value.isoformat(), field)
				elif isinstance(db_value, UUID):
					self.assertEqual(response_value, str(db_value), field)
				elif isinstance(db_value, File):
					pass
				else:
					raise
		self.assertFalse(response_data, response_data)  # no data left unchecked

	def make_user(self):
		self.user = baker.make(self.user_model, make_m2m=True)
		self.assertEqual(self.user_model.objects.count(), 1)
		db_user = User.objects.get(id=self.user.id)
		db_user.set_password(self.user.password)
		db_user.save()

	def authorize(self):
		token = baker.make(Token, user=self.user)
		self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

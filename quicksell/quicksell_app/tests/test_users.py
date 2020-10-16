"""User testing."""

from functools import partial
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from quicksell_app import models, serializers


class UsersTests(APITestCase):
	"""Testing users' actions."""

	url_user_create = reverse('user-create')
	url_user_profile = partial(reverse, 'user-detail')

	good_mail = "test@good.mail"
	good_pass = "!@34QGoodPass"

	created_user_fields = [
		field for field in serializers.User.Meta.fields
		if not getattr(serializers.User.Meta, 'extra_kwargs', {})
			.get(field, {}).get('write_only')
	]
	created_profile_fields = [
		field for field in serializers.Profile.Meta.fields
		if not getattr(serializers.Profile.Meta, 'extra_kwargs', {})
			.get(field, {}).get('write_only')
	]

	def test_create_user(self, uid=0):
		request_data = {
			'email': self.good_mail + str(uid),
			'password': self.good_pass
		}
		response = self.client.post(self.url_user_create, request_data)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(list(response.data), self.created_user_fields)
		return response

	def test_bad_request(self):
		bad_mail = "test@bad_mail"
		bad_pass = "badpass"
		for data in (
			{'email': bad_mail, 'password': bad_pass},
			{'email': self.good_mail, 'password': bad_pass},
			{'email': bad_mail, 'password': self.good_pass},
			{'email': self.good_mail},
			{'password': self.good_pass},
		):
			response = self.client.post(self.url_user_create, data)
			self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_duplicate_mail(self):
		request_data = {
			'email': self.test_create_user().data['email'],
			'password': self.good_pass
		}
		response = self.client.post(self.url_user_create, request_data)
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(models.User.objects.count(), 1)

	def test_check_profile(self, uid=None):
		if not uid:
			uid = self.test_create_user().data['id']
		response = self.client.get(self.url_user_profile(args=(uid,)))
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(list(response.data), self.created_profile_fields)

	def test_create_many_users(self):
		for i in range(100):
			response = self.test_create_user(i)
			self.test_check_profile(response.data['id'])
			self.assertEqual(models.User.objects.count(), i + 1)

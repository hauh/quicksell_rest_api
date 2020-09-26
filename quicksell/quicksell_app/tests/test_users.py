"""User testing."""

from uuid import uuid4
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from quicksell_app.models import User


class UsersTests(APITestCase):
	"""Mocking a User."""

	url_users_list = reverse('user-list')
	url_user_create = reverse('user-create')
	url_auth = reverse('auth')

	def __init__(self, *args, **kwargs):
		self.username = 'test_user_' + uuid4().hex
		self.headers = {'Authorization': None}
		super().__init__(*args, **kwargs)

	def test_create_account(self):
		data = {
			'username': self.username,
			'email': self.username + '@test.api',
			'password': 'password'
		}

		# create
		response = self.client.post(UsersTests.url_user_create, data, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(User.objects.count(), 1)
		self.assertEqual(response.data['username'], self.username)
		self.assertEqual(response.data['email'], data['email'])

		# authorize
		response = self.client.post(UsersTests.url_auth, data, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('token', response.data)

		self.headers['Authorization'] = 'Token ' + response.data['token']

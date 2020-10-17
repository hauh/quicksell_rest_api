"""User testing."""

from functools import partial

from model_bakery import baker
from django.urls import reverse
from django.conf import settings
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.test import APITestCase

from quicksell_app import models, serializers


class UsersTests(APITestCase):
	"""Testing users' actions."""

	url_auth = reverse('auth')
	url_user_create = reverse('user-create')
	url_user_profile = partial(reverse, 'user-detail')
	url_user_update = reverse('user-update')

	good_mail = "test@good.mail"
	good_pass = "!@34QGoodPass"

	user_fields = (
		'id', 'email', 'is_email_verified', 'date_joined', 'balance')
	profile_fields = (
		'user_id', 'full_name', 'about', 'online', 'rating', 'avatar', 'location')

	def __init__(self, *args, **kwargs):
		settings.PASSWORD_HASHERS = ('django.contrib.auth.hashers.MD5PasswordHasher',)  # noqa
		super().__init__(*args, **kwargs)

	def test_create_user(self, email=None):
		if not email:
			email = self.good_mail
		request_data = {'email': email, 'password': self.good_pass}
		response = self.client.post(self.url_user_create, request_data)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		user = models.User.objects.get(email=email)
		response.data['date_joined'] = parse_datetime(response.data['date_joined'])
		for field in self.user_fields:
			self.assertEqual(response.data.pop(field), getattr(user, field), field)
		self.assertDictEqual(response.data, {}, response.data)
		return {'email': user.email, 'id': user.id}

	def test_bad_request(self):
		bad_mail, bad_pass = "test@bad_mail", "badpass"
		for data in (
			{'email': bad_mail, 'password': bad_pass},
			{'email': self.good_mail, 'password': bad_pass},
			{'email': bad_mail, 'password': self.good_pass},
			{'email': self.good_mail},
			{'password': self.good_pass},
		):
			response = self.client.post(self.url_user_create, data)
			self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, data)

	def test_duplicate_mail(self):
		request_data = {
			'email': self.test_create_user()['email'],
			'password': self.good_pass
		}
		response = self.client.post(self.url_user_create, request_data)
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(models.User.objects.count(), 1)

	def test_check_profile(self, user_id=None):
		if not user_id:
			user_id = self.test_create_user()['id']
		response = self.client.get(self.url_user_profile(args=(user_id,)))
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		profile = baker.prepare(models.Profile, user__id=user_id)
		for field in self.profile_fields:
			self.assertEqual(response.data.pop(field), getattr(profile, field), field)
		self.assertDictEqual(response.data, {}, response.data)

	def test_create_many_users(self):
		for i in range(1, 100):
			user = self.test_create_user(self.good_mail + str(i))
			self.test_check_profile(user['id'])
			self.assertEqual(models.User.objects.count(), i)

	def test_authentication(self):
		request_data = {
			'username': self.test_create_user()['email'],
			'password': self.good_pass
		}
		response = self.client.post(self.url_auth, request_data)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('token', response.data)
		self.client.credentials(HTTP_AUTHORIZATION='Token ' + response.data['token'])

	def test_unauthenticated_update(self):
		response = self.client.patch(self.url_user_update, {'full_name': "Test"})
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_update_profile(self):
		read_only_fields = ('user_id', 'online', 'rating', 'location')
		profile = baker.make(
			models.Profile, make_m2m=True, _fill_optional=True, online=False)
		request_data = serializers.Profile(profile).data
		self.test_authentication()
		response = self.client.patch(self.url_user_update, request_data)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		for field in self.profile_fields:
			if field in read_only_fields:
				self.assertNotEqual(response.data[field], request_data[field], field)
			else:
				self.assertEqual(response.data[field], request_data[field], field)

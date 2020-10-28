"""User testing."""

from functools import partial

from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from model_bakery import baker

from quicksell_app.models import Profile
from quicksell_app.serializers import Profile as profile_serializer
from quicksell_app.misc import (
	base64_encode, email_verification_token_generator)

from .basetest import BaseTest


class BaseUserTest(BaseTest):
	"""Common things for testing Users, authentication, and Profiles."""

	profile_model = Profile

	url_user_profile = partial(reverse, 'user-detail')

	user_fields = ('email', 'is_email_verified', 'date_joined', 'balance')
	profile_fields = (
		'uuid', 'date_created', 'full_name', 'about',
		'online', 'rating', 'avatar', 'location'
	)

	def valid_email_variants(self, email):
		for variant in (
			email,
			email + " ",
			" " + email,
			email.upper(),
			email.lower(),
			(lambda a, b: f"{a.upper()}@{b.lower()}")(*email.split('@')),
			(lambda a, b: f"{a.lower()}@{b.upper()}")(*email.split('@')),
		):
			yield variant


class TestUserCreation(BaseUserTest):
	"""Testing various events when creating account."""

	url_user_create = reverse('user-create')

	good_mail = "test@good.mail"
	good_pass = "!@34GoodPass"

	def generate_confirm_email_url(self, user):
		return reverse('email-confirm', args=(
			base64_encode(user.email),
			email_verification_token_generator.make_token(user)
		))

	def test_create_user(self):
		self.assertEqual(self.user_model.objects.count(), 0)
		data = {'email': self.good_mail, 'password': self.good_pass}
		response = self.POST(self.url_user_create, status.HTTP_201_CREATED, data)
		self.assertEqual(self.user_model.objects.count(), 1)
		self.assertTupleEqual(tuple(response.data), self.user_fields)
		user = self.user_model.objects.get(email=response.data['email'])
		self.field_by_field_compare(response.data, user, self.user_fields)

	def test_invalid_signup(self):
		for data in (
			{'email': "test@bad_mail", 'password': "badpass"},
			{'email': self.good_mail, 'password': "badpass"},
			{'email': self.good_mail, 'password': ""},
			{'email': self.good_mail},
			{'email': "test@bad_mail", 'password': self.good_pass},
			{'email': "", 'password': self.good_pass},
			{'password': self.good_pass},
		):
			self.POST(self.url_user_create, status.HTTP_400_BAD_REQUEST, data)
			self.assertEqual(self.user_model.objects.count(), 0)

	def test_duplicate_email(self):
		self.make_user()
		for email in self.valid_email_variants(self.user.email):
			data = {'email': email, 'password': self.good_pass}
			self.POST(self.url_user_create, status.HTTP_400_BAD_REQUEST, data)
			self.assertEqual(self.user_model.objects.count(), 1)

	def test_confirm_email(self):
		self.make_user()
		self.assertFalse(self.user.is_email_verified)
		confirm_email_url = self.generate_confirm_email_url(self.user)
		# GET confirmation page
		self.GET(confirm_email_url, status.HTTP_200_OK)
		# PATCH from that page (invalid token)
		self.PATCH(confirm_email_url[:-2] + '/', status.HTTP_400_BAD_REQUEST)
		# PATCH from that page (valid token)
		self.PATCH(confirm_email_url, status.HTTP_200_OK)
		self.user.refresh_from_db()
		self.assertTrue(self.user.is_email_verified)
		# Token is no longer valid
		self.PATCH(confirm_email_url, status.HTTP_400_BAD_REQUEST)

	def test_view_profile(self):
		self.make_user()
		profile = self.user.profile
		profile_url = self.url_user_profile(args=(profile.uuid,))
		response = self.GET(profile_url, status.HTTP_200_OK)
		self.assertTupleEqual(tuple(response.data), self.profile_fields)
		self.field_by_field_compare(response.data, profile, self.profile_fields)

	def test_create_many_users(self):
		users = baker.prepare(self.user_model, _quantity=100)
		for user in users:
			# Create user
			data = {'email': user.email, 'password': user.password}
			response = self.POST(self.url_user_create, status.HTTP_201_CREATED, data)
			self.assertTupleEqual(tuple(response.data), self.user_fields)
			# Confirm email
			created_user = self.user_model.objects.get(email=response.data['email'])
			confirm_email_url = self.generate_confirm_email_url(created_user)
			self.GET(confirm_email_url, status.HTTP_200_OK)
			self.PATCH(confirm_email_url, status.HTTP_200_OK)
			# Check profile
			profile_url = self.url_user_profile(args=(created_user.profile.uuid,))
			response = self.GET(profile_url, status.HTTP_200_OK)
			self.assertTupleEqual(tuple(response.data), self.profile_fields)
		self.assertEqual(self.user_model.objects.count(), len(users))


class TestUserAuthentication(BaseUserTest):
	"""Testing User authentication."""

	url_auth = reverse('auth')

	def setUp(self):
		super().setUp()
		self.make_user()

	def test_authentication(self):
		for username in self.valid_email_variants(self.user.email):
			data = {'username': username, 'password': self.user.password}
			response = self.POST(self.url_auth, status.HTTP_200_OK, data)
			self.assertIn('token', response.data)

	def test_invalid_credentials(self):
		for data in (
			{'username': self.user.email, 'password': "wrong pass"},
			{'username': "email@doesn't.exist", 'password': self.user.password}
		):
			response = self.POST(self.url_auth, status.HTTP_400_BAD_REQUEST, data)
			self.assertNotIn('token', response.data)


class TestUpdateAccountActions(BaseUserTest):
	"""Testing User and Profile updates."""

	url_user_update = reverse('user-update')

	def setUp(self):
		super().setUp()
		self.make_user()
		self.profile = self.user.profile
		token = baker.make(Token, user=self.user)
		self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

	def test_update_field(self):
		data = {'full_name': "Test User"}
		response = self.PATCH(self.url_user_update, status.HTTP_200_OK, data)
		self.profile.refresh_from_db()
		self.assertEqual(response.data['full_name'], data['full_name'])
		self.assertEqual(response.data['full_name'], self.profile.full_name)

	def test_unauthenticated_edit(self):
		self.client.credentials()
		data = {'full_name': "Should Not Change"}
		self.PATCH(self.url_user_update, status.HTTP_401_UNAUTHORIZED, data)
		self.profile.refresh_from_db()
		self.assertNotEqual(data['full_name'], self.profile.full_name)

	def test_update_profile(self):
		read_only_fields = {'uuid', 'online', 'rating', 'location'}
		profile_replace = baker.prepare(
			self.profile_model, _fill_optional=True, _save_related=True, online=False)
		data = profile_serializer(profile_replace).data
		response = self.PATCH(self.url_user_update, status.HTTP_200_OK, data)
		self.assertTupleEqual(tuple(response.data), self.profile_fields)
		self.profile.refresh_from_db()
		unchanged = {field: response.data.pop(field) for field in read_only_fields}
		self.field_by_field_compare(unchanged, self.profile, read_only_fields)
		changed_fields = set(self.profile_fields) - read_only_fields
		self.field_by_field_compare(response.data, self.profile, changed_fields)

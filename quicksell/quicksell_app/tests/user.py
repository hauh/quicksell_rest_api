"""User testing."""

from functools import partial
from datetime import timedelta

from django.urls import reverse
from django.core import mail
from django.conf import settings
from django.core.cache import cache

from rest_framework import status
from model_bakery import baker

from quicksell_app.models import Profile
from quicksell_app.serializers import Profile as profile_serializer

from .basetest import BaseTest


class BaseUserTest(BaseTest):
	"""Common things for endpoints at `api/users/`."""

	profile_model = Profile

	url_user_create = reverse('user-create')
	url_auth = reverse('login')
	url_user_profile = partial(reverse, 'profile-detail')
	url_password_update = reverse('password-update')
	url_profile_update = reverse('profile-update')

	emails_from = settings.DEFAULT_FROM_EMAIL

	good_mail = "test@good.mail"
	good_pass = "!@34GoodPass"

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
	"""api/users/new/"""

	def test_create_user(self):
		self.assertEqual(self.user_model.objects.count(), 0)
		data = {'email': self.good_mail, 'password': self.good_pass}
		response = self.POST(self.url_user_create, status.HTTP_201_CREATED, data)
		self.assertEqual(self.user_model.objects.count(), 1)
		self.assertTupleEqual(tuple(response.data), self.user_fields)
		user = self.user_model.objects.get(email=response.data['email'])
		self.field_by_field_compare(response.data, user, self.user_fields)
		# checking email confirmation
		self.assertEqual(len(mail.outbox), 1)
		email = mail.outbox[0]
		self.assertEqual(email.from_email, self.emails_from)
		self.assertEqual(email.to, [data['email']])
		self.assertEqual(email.subject, "Activate Your Quicksell Account")
		self.assertTrue(email.body.startswith("Click the link to confirm"))

	def test_invalid_signup(self):
		for data in (
			{'email': "test@bad_mail", 'password': "badpass"},
			{'email': self.good_mail, 'password': "badpass"},
			{'email': self.good_mail, 'password': ""},
			{'email': self.good_mail, 'password': None},
			{'email': self.good_mail},
			{'email': "test@bad_mail", 'password': self.good_pass},
			{'email': "", 'password': self.good_pass},
			{'email': None, 'password': self.good_pass},
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
		# registering new user
		data = {'email': self.good_mail, 'password': self.good_pass}
		response = self.POST(self.url_user_create, status.HTTP_201_CREATED, data)
		user = self.user_model.objects.get(email=response.data['email'])
		self.assertFalse(user.is_email_verified)
		confirm_email_url = mail.outbox[0].body.split('\n')[1]
		# GET confirmation page
		self.GET(confirm_email_url, status.HTTP_200_OK)
		# PATCH from that page (invalid token)
		self.PATCH(confirm_email_url[:-2] + '/', status.HTTP_400_BAD_REQUEST)
		# PATCH from that page (valid token)
		self.PATCH(confirm_email_url, status.HTTP_200_OK)
		user.refresh_from_db()
		self.assertTrue(user.is_email_verified)
		# token is no longer valid
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
			# create user
			data = {'email': user.email, 'password': user.password}
			response = self.POST(self.url_user_create, status.HTTP_201_CREATED, data)
			self.assertTupleEqual(tuple(response.data), self.user_fields)
			# confirm email
			confirm_email_url = mail.outbox[-1].body.split('\n')[1]
			self.GET(confirm_email_url, status.HTTP_200_OK)
			self.PATCH(confirm_email_url, status.HTTP_200_OK)
		self.assertEqual(self.user_model.objects.count(), len(users))


class TestPasswordReset(BaseUserTest):
	"""api/users/password/reset/"""

	def setUp(self):
		super().setUp()
		cache.clear()
		self.make_user()

	def test_invalid_email(self):
		data = {'email': "invalid@mail"}
		self.POST(self.url_password_update, status.HTTP_400_BAD_REQUEST, data)

	def test_unregistered_email(self):
		data = {'email': self.good_mail}
		self.POST(self.url_password_update, status.HTTP_202_ACCEPTED, data)
		self.assertEqual(len(mail.outbox), 1)
		email = mail.outbox[0]
		self.assertEqual(email.from_email, self.emails_from)
		self.assertEqual(email.to, [data['email']])
		self.assertEqual(email.subject, "Quicksell Account Notification")
		self.assertTrue(email.body.startswith("Someone requested to reset password"))

	def test_valid_email(self):
		data = {'email': self.user.email}
		self.assertTrue(self.user.has_usable_password())
		self.assertIsNone(self.user.password_reset_code)
		self.assertIsNone(self.user.password_reset_request_time)
		# requesting code
		self.POST(self.url_password_update, status.HTTP_202_ACCEPTED, data)
		self.user.refresh_from_db()
		self.assertIsNotNone(self.user.password_reset_code)
		self.assertIsNotNone(self.user.password_reset_request_time)
		# checking email
		self.assertEqual(len(mail.outbox), 1)
		email = mail.outbox[0]
		self.assertEqual(email.from_email, self.emails_from)
		self.assertEqual(email.to, [data['email']])
		self.assertEqual(email.subject, "Quicksell Account Notification")
		self.assertTrue(email.body.startswith("Enter this code in the app"))
		code = int(email.body.split('\n')[1])
		self.assertEqual(self.user.password_reset_code, code)
		# reseting password
		data |= {'code': code}
		response = self.DELETE(self.url_password_update, status.HTTP_200_OK, data)
		self.DELETE(self.url_password_update, status.HTTP_401_UNAUTHORIZED, data)
		self.assertIn('token', response.data)
		self.user.refresh_from_db()
		self.assertFalse(self.user.has_usable_password())
		self.assertIsNone(self.user.password_reset_code)
		self.assertIsNone(self.user.password_reset_request_time)

	def test_invalid_request(self):
		# invalid data
		for data in (
			{'email': self.user.email, 'code': ""},
			{'email': self.user.email, 'code': None},
			{'email': self.user.email},
			{'email': "invalid@mail", 'code': 111777},
			{'code': 111777},
			{},
		):
			self.DELETE(self.url_password_update, status.HTTP_400_BAD_REQUEST, data)
		cache.clear()
		# request to reset before requesting code
		data = {'email': self.user.email, 'code': 123123}
		self.DELETE(self.url_password_update, status.HTTP_401_UNAUTHORIZED, data)
		# wrong code
		self.POST(self.url_password_update, status.HTTP_202_ACCEPTED, data)
		data['code'] = int(mail.outbox[0].body.split('\n')[1]) + 1
		self.DELETE(self.url_password_update, status.HTTP_401_UNAUTHORIZED, data)
		data['code'] -= 1
		self.DELETE(self.url_password_update, status.HTTP_200_OK, data)
		cache.clear()
		# expired code
		self.POST(self.url_password_update, status.HTTP_202_ACCEPTED, data)
		data['code'] = int(mail.outbox[0].body.split('\n')[1])
		self.user.refresh_from_db()
		self.user.password_reset_request_time -= timedelta(seconds=3601)
		self.user.save()
		self.DELETE(self.url_password_update, status.HTTP_401_UNAUTHORIZED, data)
		# code without timestamp
		self.POST(self.url_password_update, status.HTTP_202_ACCEPTED, data)
		data['code'] = int(mail.outbox[0].body.split('\n')[1])
		self.user.password_reset_request_time = None
		self.user.save()
		self.DELETE(self.url_password_update, status.HTTP_401_UNAUTHORIZED, data)

	def test_throttling(self):
		hourly_limit = 15
		for _ in range(hourly_limit):
			self.DELETE(self.url_password_update, status.HTTP_400_BAD_REQUEST, {})
		for _ in range(5):
			self.DELETE(self.url_password_update, status.HTTP_429_TOO_MANY_REQUESTS, {})
		self.assertEqual(len(mail.outbox), 0)


class TestUserAuthentication(BaseUserTest):
	"""api/users/login/"""

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


class TestPasswordUpdate(BaseUserTest):
	"""api/users/password/update/"""

	new_pass = "New$#21Pass"

	def setUp(self):
		super().setUp()
		self.make_user()
		self.authorize()

	def test_change_password(self):
		# changing password
		data = {'old_password': self.user.password, 'new_password': self.new_pass}
		response = self.PUT(self.url_password_update, status.HTTP_200_OK, data)
		self.assertFalse(response.data, response.data)  # response.data is empty
		# password is valid, but auth token is not anymore
		data = {'old_password': self.new_pass, 'new_password': self.user.password}
		self.PUT(self.url_password_update, status.HTTP_401_UNAUTHORIZED, data)
		# authorizing and changing password back
		self.authorize()
		data = {'old_password': self.new_pass, 'new_password': self.user.password}
		response = self.PUT(self.url_password_update, status.HTTP_200_OK, data)
		self.assertFalse(response.data, response.data)  # response.data is empty

	def test_invalid_request(self):
		for data in (
			{'old_password': self.user.password, 'new_password': "badpass"},
			{'old_password': self.user.password, 'new_password': ""},
			{'old_password': self.user.password, 'new_password': None},
			{'old_password': self.user.password},
			{},
		):
			self.POST(self.url_password_update, status.HTTP_400_BAD_REQUEST, data)

	def test_set_password_after_reset(self):
		# trying to set new password without providing old one
		pass_data = {'new_password': self.new_pass}
		self.PUT(self.url_password_update, status.HTTP_401_UNAUTHORIZED, pass_data)
		# requesting password reset
		data = {'email': self.user.email}
		self.POST(self.url_password_update, status.HTTP_202_ACCEPTED, data)
		data |= {'code': int(mail.outbox[0].body.split('\n')[1])}
		response = self.DELETE(self.url_password_update, status.HTTP_200_OK, data)
		self.assertIn('token', response.data)
		# user now has no password, API will accept any if authorized with new token
		self.PUT(self.url_password_update, status.HTTP_401_UNAUTHORIZED, pass_data)
		self.client.credentials(HTTP_AUTHORIZATION='Token ' + response.data['token'])
		self.PUT(self.url_password_update, status.HTTP_200_OK, pass_data)
		self.authorize()
		# changing password again requires both old and new passwords
		self.PUT(self.url_password_update, status.HTTP_401_UNAUTHORIZED, pass_data)
		pass_data |= {'old_password': self.new_pass}
		self.PUT(self.url_password_update, status.HTTP_200_OK, pass_data)


class TestUpdateProfileActions(BaseUserTest):
	"""api/users/profile/"""

	def setUp(self):
		super().setUp()
		self.make_user()
		self.authorize()
		self.profile = self.user.profile

	def test_update_field(self):
		data = {'full_name': "Test User"}
		response = self.PATCH(self.url_profile_update, status.HTTP_200_OK, data)
		self.profile.refresh_from_db()
		self.assertEqual(response.data['full_name'], data['full_name'])
		self.assertEqual(response.data['full_name'], self.profile.full_name)

	def test_unauthenticated_edit(self):
		self.client.credentials()
		data = {'full_name': "Should Not Change"}
		self.PATCH(self.url_profile_update, status.HTTP_401_UNAUTHORIZED, data)
		self.profile.refresh_from_db()
		self.assertNotEqual(data['full_name'], self.profile.full_name)

	def test_update_profile(self):
		read_only_fields = {'uuid', 'online', 'rating', 'location'}
		profile_replace = baker.prepare(
			self.profile_model, _fill_optional=True, _save_related=True, online=False)
		data = profile_serializer(profile_replace).data
		response = self.PATCH(self.url_profile_update, status.HTTP_200_OK, data)
		self.assertTupleEqual(tuple(response.data), self.profile_fields)
		self.profile.refresh_from_db()
		unchanged = {field: response.data.pop(field) for field in read_only_fields}
		self.field_by_field_compare(unchanged, self.profile, read_only_fields)
		changed_fields = set(self.profile_fields) - read_only_fields
		self.field_by_field_compare(response.data, self.profile, changed_fields)

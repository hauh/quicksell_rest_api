"""User testing."""

from datetime import datetime, timedelta
from functools import partial

from django.core import mail
from django.core.cache import cache
from django.urls import reverse
from model_bakery import baker
from rest_framework.status import (
	HTTP_200_OK, HTTP_201_CREATED, HTTP_202_ACCEPTED, HTTP_400_BAD_REQUEST,
	HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND,
	HTTP_429_TOO_MANY_REQUESTS
)

from quicksell_app import models
from .basetest import BaseTest


class BaseUserTest(BaseTest):
	"""Common things for endpoints at `api/users/`."""

	url_user = reverse('user')
	url_login = reverse('login')
	url_password = reverse('password')
	url_profile = reverse('profile')
	url_profile_detail = partial(reverse, 'profile-detail')

	good_mail = "test@good.mail"
	good_pass = "!@34GoodPass"
	good_pass2 = "New$#21Pass"
	valid_reg_data = {
		'email': good_mail,
		'password': good_pass,
		'full_name': "Qucksell User",
		'fcm_id': 'some_fcm_id' * 10,
		'location': {
			'coordinates': "12.345678, 87.654321",
			'address': "Test avenue 42"
		}
	}

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


class TestAuthentication(BaseUserTest):
	"""POST api/users/login/"""

	def setUp(self):
		super().setUp()
		self.make_user()

	def test_authenticate(self):
		for username in self.valid_email_variants(self.user.email):
			data = {'username': username, 'password': self.user_pass}
			response = self.POST(self.url_login, HTTP_200_OK, data)
			self.assertIn('token', response.data)
			self.user.refresh_from_db(fields=('auth_token',))
			self.assertEqual(str(self.user.auth_token), response.data['token'])

	def test_invalid_credentials(self):
		for data in (
			{'username': self.user.email, 'password': "wrong pass"},
			{'username': "email@doesn't.exist", 'password': self.user.password},
			{'username': self.user.email},
		):
			response = self.POST(self.url_login, HTTP_400_BAD_REQUEST, data)
			self.assertNotIn('token', response.data)


class TestUserCreation(BaseUserTest):
	"""POST, GET api/users/"""

	def test_create_user(self):
		self.assertEqual(self.user_model.objects.count(), 0)
		response = self.POST(self.url_user, HTTP_201_CREATED, self.valid_reg_data)
		self.assertEqual(self.user_model.objects.count(), 1)
		user = self.user_model.objects.get(email=response.data['email'])
		self.assertDictEqual(response.data, user.serialize())
		# checking email confirmation
		self.assertEqual(len(mail.outbox), 1)
		email = mail.outbox[0]
		self.assertEqual(email.from_email, self.emails_from)
		self.assertEqual(email.to, [self.valid_reg_data['email']])
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
			{'location': 'bad location'},
			{'location': {'coordinates': 'bad coords', 'address': 'ok'}}
		):
			self.POST(self.url_user, HTTP_400_BAD_REQUEST, data)
			self.assertEqual(self.user_model.objects.count(), 0)

	def test_duplicate_email(self):
		self.make_user()
		for email in self.valid_email_variants(self.user.email):
			data = {'email': email, 'password': self.good_pass}
			self.POST(self.url_user, HTTP_400_BAD_REQUEST, data)
			self.assertEqual(self.user_model.objects.count(), 1)

	def test_get_self_account(self):
		self.make_user()
		# who are you?
		response = self.GET(self.url_user, HTTP_401_UNAUTHORIZED)
		self.assertIn('detail', response.data)
		response.data.pop('detail')
		self.assertFalse(response.data)
		# set token and check again
		self.authorize()
		response = self.GET(self.url_user, HTTP_200_OK)
		self.assertDictEqual(response.data, self.user.serialize())


class TestEmailConfirmation(BaseUserTest):
	"""GET, PATCH api/users/password/"""

	def test_confirm_email(self):
		# registering new user
		response = self.POST(self.url_user, HTTP_201_CREATED, self.valid_reg_data)
		self.assertIn('email', response.data)
		user = self.user_model.objects.get(email=response.data['email'])
		self.assertFalse(user.is_email_verified)
		confirm_email_url = mail.outbox[0].body.split('\n')[1]
		# GET confirmation page
		self.GET(confirm_email_url, HTTP_200_OK)
		# PATCH from that page (invalid token)
		self.PATCH(confirm_email_url[:-2] + '/', HTTP_400_BAD_REQUEST)
		# PATCH from that page (valid token)
		self.PATCH(confirm_email_url, HTTP_200_OK)
		user.refresh_from_db()
		self.assertTrue(user.is_email_verified)
		# confirmation link is no longer valid
		self.PATCH(confirm_email_url, HTTP_400_BAD_REQUEST)


class TestPasswordActions(BaseUserTest):
	"""POST, PUT, DELETE api/users/password/"""

	def setUp(self):
		super().setUp()
		self.make_user()
		cache.clear()

	def test_reset_password_wrong_email(self):
		data = {'email': self.good_mail}
		self.POST(self.url_password, HTTP_202_ACCEPTED, data)
		self.assertEqual(len(mail.outbox), 1)
		email = mail.outbox[0]
		self.assertEqual(email.from_email, self.emails_from)
		self.assertEqual(email.to, [data['email']])
		self.assertEqual(email.subject, "Quicksell Account Notification")
		self.assertTrue(email.body.startswith("Someone made a request to reset"))

	def test_reset_password_valid_email(self):
		data = {'email': self.user.email}
		self.assertTrue(self.user.has_usable_password())
		self.assertIsNone(self.user.password_reset_code)
		self.assertIsNone(self.user.password_reset_request_time)
		# requesting code
		self.POST(self.url_password, HTTP_202_ACCEPTED, data)
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
		response = self.DELETE(self.url_password, HTTP_200_OK, data)
		self.DELETE(self.url_password, HTTP_401_UNAUTHORIZED, data)
		self.assertIn('token', response.data)
		self.user.refresh_from_db()
		self.assertFalse(self.user.has_usable_password())
		self.assertIsNone(self.user.password_reset_code)
		self.assertIsNone(self.user.password_reset_request_time)

	def test_reset_password_bad_request(self):
		for data in (
			{'email': self.user.email, 'code': ""},
			{'email': self.user.email, 'code': "wrong"},
			{'email': self.user.email, 'code': None},
			{'email': self.user.email},
			{'email': "invalid@mail", 'code': 111777},
			{'email': "invalid@mail"},
			{'code': 111777},
			{},
		):
			self.DELETE(self.url_password, HTTP_400_BAD_REQUEST, data)

	def test_reset_password_wrong_code(self):
		# request to reset before requesting code
		data = {'email': self.user.email, 'code': 123123}
		self.DELETE(self.url_password, HTTP_401_UNAUTHORIZED, data)
		# wrong code
		self.POST(self.url_password, HTTP_202_ACCEPTED, data)
		data['code'] = int(mail.outbox[0].body.split('\n')[1]) + 1
		self.DELETE(self.url_password, HTTP_401_UNAUTHORIZED, data)
		data['code'] -= 1
		self.DELETE(self.url_password, HTTP_200_OK, data)

	def test_reset_password_wrong_date(self):
		# expired code
		data = {'email': self.user.email}
		self.POST(self.url_password, HTTP_202_ACCEPTED, data)
		data['code'] = int(mail.outbox[0].body.split('\n')[1])
		self.user.refresh_from_db()
		self.user.password_reset_request_time -= timedelta(seconds=3601)
		self.user.save()
		self.DELETE(self.url_password, HTTP_403_FORBIDDEN, data)
		# code without timestamp
		self.POST(self.url_password, HTTP_202_ACCEPTED, data)
		data['code'] = int(mail.outbox[0].body.split('\n')[1])
		self.user.password_reset_request_time = None
		self.user.save()
		self.DELETE(self.url_password, HTTP_403_FORBIDDEN, data)

	def test_change_password(self):
		# changing password, need auth
		data = {'old_password': self.user_pass, 'new_password': self.good_pass2}
		response = self.PUT(self.url_password, HTTP_401_UNAUTHORIZED, data)
		self.authorize()
		response = self.PUT(self.url_password, HTTP_200_OK, data)
		self.assertFalse(response.data, response.data)  # response.data is empty
		# password is valid, but auth token is not anymore
		data = {'old_password': self.good_pass2, 'new_password': self.user_pass}
		self.PUT(self.url_password, HTTP_401_UNAUTHORIZED, data)
		# authorizing and changing password back
		self.authorize()
		data = {'old_password': self.good_pass2, 'new_password': self.user.password}
		response = self.PUT(self.url_password, HTTP_200_OK, data)
		self.assertFalse(response.data, response.data)  # response.data is empty

	def test_change_password_bad_request(self):
		for data in (
			{'old_password': self.user.password, 'new_password': "badpass"},
			{'old_password': self.user.password, 'new_password': ""},
			{'old_password': self.user.password, 'new_password': None},
			{'old_password': self.user.password},
			{},
		):
			self.POST(self.url_password, HTTP_400_BAD_REQUEST, data)

	def test_reset_password_and_set_new(self):
		# trying to set new password without providing old one
		pass_data = {'new_password': self.good_pass2}
		self.PUT(self.url_password, HTTP_401_UNAUTHORIZED, pass_data)
		# requesting password reset
		data = {'email': self.user.email}
		self.POST(self.url_password, HTTP_202_ACCEPTED, data)
		data |= {'code': int(mail.outbox[0].body.split('\n')[1])}
		response = self.DELETE(self.url_password, HTTP_200_OK, data)
		self.assertIn('token', response.data)
		# user now has no password, API will accept any if authorized with new token
		self.PUT(self.url_password, HTTP_401_UNAUTHORIZED, pass_data)
		self.client.credentials(HTTP_AUTHORIZATION='Token ' + response.data['token'])
		self.PUT(self.url_password, HTTP_200_OK, pass_data)
		# check login with new pass, token no longer valid
		self.client.credentials()
		data = {'username': self.user.email, 'password': self.good_pass2}
		response = self.POST(self.url_login, HTTP_200_OK, data)
		self.assertIn('token', response.data)
		self.client.credentials(HTTP_AUTHORIZATION='Token ' + response.data['token'])
		# changing password again requires both old and new passwords
		pass_data['new_password'] = self.good_pass
		self.PUT(self.url_password, HTTP_401_UNAUTHORIZED, pass_data)
		pass_data |= {'old_password': self.good_pass2}
		self.PUT(self.url_password, HTTP_200_OK, pass_data)
		self.authorize()
		# check login with new pass again
		data = {'username': self.user.email, 'password': self.good_pass}
		self.POST(self.url_login, HTTP_200_OK, data)
		self.assertIn('token', response.data)

	def test_throttling(self):
		hourly_limit = 15
		for _ in range(hourly_limit):
			self.DELETE(self.url_password, HTTP_400_BAD_REQUEST, {})
		for _ in range(5):
			self.DELETE(self.url_password, HTTP_429_TOO_MANY_REQUESTS, {})
		self.assertEqual(len(mail.outbox), 0)


class TestProfileActions(BaseUserTest):
	"""GET, PATCH api/profiles/"""

	def setUp(self):
		super().setUp()
		self.make_user()
		self.authorize()
		self.profile = self.user.profile

	def test_get_profile(self):
		profile_url = self.url_profile_detail(args=('invalid_uuid',))
		self.GET(profile_url, HTTP_404_NOT_FOUND)
		valid_uuid = self.user.profile.serialize()['uuid']
		not_existing_url = self.url_profile_detail(args=(valid_uuid[:-3] + 'abs',))
		self.GET(not_existing_url, HTTP_404_NOT_FOUND)
		for user in baker.make(self.user_model, make_m2m=True, _quantity=10):
			serialized_profile = user.profile.serialize()
			profile_url = self.url_profile_detail(args=(serialized_profile['uuid'],))
			response = self.GET(profile_url, HTTP_200_OK)
			self.assertDictEqual(response.data, serialized_profile)

	def test_query_profiles(self):
		check_result = partial(self.query_paginated_result, self.url_profile)
		q = 111
		baker.make(models.Profile, _quantity=q, rating=0, full_name="++TEST++")
		baker.make(models.Profile, _quantity=q, rating=10, online=False)
		baker.make(models.Profile, _quantity=q, rating=20, full_name="T++T")
		max_q = q * 3 + 1
		self.profile.rating = 12
		self.profile.save()
		self.assertEqual(models.Profile.objects.count(), max_q)

		check_result({'min_rating': 10}, max_q - q)
		check_result({'min_rating': 20}, q)

		check_result({'full_name': "++TEST++"}, q)
		check_result({'full_name': "TEST"}, q)
		check_result({'full_name': "test"}, q)
		check_result({'full_name': "++"}, q * 2)
		check_result({'full_name': "NOPE"}, 0)

		check_result({'online': True}, max_q - q)
		check_result({'online': False}, q)

		now = datetime.now()
		reg = {'registered_before': now.strftime("%Y-%m-%d")}
		check_result(reg, 0)
		reg = {'registered_before': (now + timedelta(days=1)).strftime("%Y-%m-%d")}
		check_result(reg, max_q)

		check_result({'min_rating': 10, 'online': False}, q)
		check_result({'min_rating': 10, 'online': True}, q + 1)
		check_result({'full_name': "++", 'online': False}, 0)
		check_result({'full_name': "++", 'min_rating': 12}, q)

		data = {'min_rating': 10, 'order_by': 'rating'}
		first_page, last_page = check_result(data, max_q - q)
		self.assertEqual(first_page.data['results'][0]['rating'], 10)
		self.assertEqual(last_page.data['results'][-1]['rating'], 20)

		data = {'min_rating': 10, 'order_by': '-rating'}
		first_page, last_page = check_result(data, max_q - q)
		self.assertEqual(first_page.data['results'][0]['rating'], 20)
		self.assertEqual(last_page.data['results'][-1]['rating'], 10)

	def test_update_profile(self):
		# edit name
		data = {'full_name': "Test User"}
		response = self.PATCH(self.url_profile, HTTP_200_OK, data)
		self.profile.refresh_from_db()
		self.assertDictEqual(response.data, self.profile.serialize())
		# edit everything
		filled_profile = baker.prepare(
			models.Profile, _fill_optional=True, _save_related=True, online=False,
			location=models.Location.objects.get(pk=models.Location.default_pk())
		)
		new_data = filled_profile.serialize()
		response = self.PATCH(self.url_profile, HTTP_200_OK, new_data)
		self.profile.refresh_from_db()
		self.assertDictEqual(response.data, self.profile.serialize())
		# unauthenticated edit
		self.client.credentials()
		data = {'full_name': "Should not change"}
		self.PATCH(self.url_profile, HTTP_401_UNAUTHORIZED, data)
		self.profile.refresh_from_db()
		self.assertNotEqual(data['full_name'], self.profile.full_name)


class TestUserFull(BaseUserTest):
	"""Test all User's actions together."""

	def test_new_users_actions(self):
		user_count = 100
		for i in range(1, user_count):
			# create user
			data = {**self.valid_reg_data}
			for key in ('email', 'fcm_id'):
				data[key] += str(i)
			response = self.POST(self.url_user, HTTP_201_CREATED, data)
			user = self.user_model.objects.get(email=data['email'])
			self.assertDictEqual(response.data, user.serialize())
			# confirm email
			confirm_email_url = mail.outbox[-1].body.split('\n')[1]
			self.GET(confirm_email_url, HTTP_200_OK)
			self.PATCH(confirm_email_url, HTTP_200_OK)
			user.refresh_from_db()
			self.assertTrue(user.is_email_verified)
			# authorize
			data = {'username': user.email, 'password': self.good_pass}
			response = self.POST(self.url_login, HTTP_200_OK, data)
			self.assertIn('token', response.data)
			self.client.credentials(
				HTTP_AUTHORIZATION="Token " + response.data['token'])
			# update profile
			data = {'full_name': "Dummy", 'about': "Test user."}
			response = self.PATCH(self.url_profile, HTTP_200_OK, data)
			user.profile.refresh_from_db()
			self.assertDictEqual(response.data, user.profile.serialize())
			# update password
			data = {'old_password': self.good_pass, 'new_password': self.good_pass2}
			self.PUT(self.url_password, HTTP_200_OK, data)
			self.client.credentials()
			data = {'username': user.email, 'password': self.good_pass2}
			response = self.POST(self.url_login, HTTP_200_OK, data)
			self.assertIn('token', response.data)

			self.assertEqual(self.user_model.objects.count(), i)

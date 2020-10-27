"""Tests."""

from django.conf import settings
from model_bakery import baker

from .user import (
	TestUserCreation, TestUserAuthentication, TestUpdateAccountActions)
# from .listing import UsersTests


settings.PASSWORD_HASHERS = ('django.contrib.auth.hashers.MD5PasswordHasher',)
baker.generators.add(
	'quicksell_app.utils.LowercaseEmailField', baker.random_gen.gen_email)

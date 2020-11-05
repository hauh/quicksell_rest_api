"""Tests."""

from django.conf import settings
from model_bakery import baker

from .user import (
	TestAuthentication, TestUserCreation, TestEmailConfirmation,
	TestPasswordActions, TestProfileActions, TestUserFull
)
# from .listing import UsersTests


settings.PASSWORD_HASHERS = ('django.contrib.auth.hashers.MD5PasswordHasher',)
settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

baker.generators.add(
	'quicksell_app.models.user.LowercaseEmailField',
	baker.random_gen.gen_email
)

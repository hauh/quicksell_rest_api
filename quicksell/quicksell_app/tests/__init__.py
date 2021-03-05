"""Tests."""

from django.conf import settings
from model_bakery import baker

from .chat import TestChat, TestMessage
from .listing import TestListingCreation, TestListingEdit, TestListingFull
from .user import (
	TestAuthentication, TestEmailConfirmation, TestPasswordActions,
	TestProfileActions, TestUserCreation, TestUserFull
)


baker.generators.add(
	'quicksell_app.models.user.LowercaseEmailField',
	baker.random_gen.gen_email
)
